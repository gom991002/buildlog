import { useEffect, useRef, useState } from 'react'
import { errorMessage, fieldErrors } from '../api/client.js'
import { deleteMaterial, listMaterials, uploadMaterial } from '../api/materials.js'
import './MaterialsPage.css'

// Same rules as the server (plan.md section 10); the server makes the final decision.
const TITLE_MAX = 100
const MEMO_MAX = 1000
const MIB = 1024 * 1024
const FILE_RULES = {
  png: { kind: '이미지', limit: 5 * MIB },
  jpg: { kind: '이미지', limit: 5 * MIB },
  jpeg: { kind: '이미지', limit: 5 * MIB },
  mp4: { kind: '영상', limit: 30 * MIB },
}
const ACCEPT = '.png,.jpg,.jpeg,.mp4,image/png,image/jpeg,video/mp4'

// Characters are counted the way the server counts them (code points, not UTF-16 units).
const length = (text) => Array.from(text).length

function fileRule(file) {
  const extension = file.name.split('.').pop().toLowerCase()
  return file.name.includes('.') ? FILE_RULES[extension] : undefined
}

function fileError(file) {
  if (!file) return '올릴 파일을 선택해 주세요.'
  const rule = fileRule(file)
  if (!rule) return 'PNG·JPG 이미지 또는 MP4 영상만 올릴 수 있습니다.'
  if (file.size === 0) return '빈 파일은 올릴 수 없습니다.'
  if (file.size > rule.limit) return '이미지는 5MB, 영상은 30MB까지 올릴 수 있습니다.'
  return ''
}

function formatSize(bytes) {
  return bytes >= MIB ? `${(bytes / MIB).toFixed(1)}MB` : `${Math.max(1, Math.round(bytes / 1024))}KB`
}

function formatDate(iso) {
  return new Date(iso).toLocaleString('ko-KR', {
    timeZone: 'Asia/Seoul',
    dateStyle: 'medium',
    timeStyle: 'short',
  })
}

const AI_MESSAGES = {
  failed: 'AI 요약을 만들지 못했습니다. 자료는 정상적으로 저장되었습니다.',
  disabled: 'AI 요약이 꺼져 있습니다. 서버 .env에 OPENAI_API_KEY를 넣으면 이후 올리는 자료부터 요약됩니다.',
}

// The preview loads the original through the same login-checked address as "원본 보기".
// lazy / preload="metadata" keep the list from downloading every file at once.
function MaterialPreview({ material }) {
  const [failed, setFailed] = useState(false)
  const isVideo = material.content_type.startsWith('video/')

  if (failed) {
    return (
      <div className="material-preview material-preview-missing" role="img" aria-label="미리보기를 불러오지 못했습니다">
        {isVideo ? '▶' : '▣'}
        <span>미리보기를 불러오지 못했습니다</span>
      </div>
    )
  }
  // A small thumbnail; clicking it opens the original (videos play there).
  return (
    <a className="material-preview-link" href={material.file_url} target="_blank" rel="noreferrer">
      {isVideo ? (
        <>
          {/* #t=0.1 makes browsers draw a frame instead of a blank box. */}
          <video
            className="material-preview"
            src={`${material.file_url}#t=0.1`}
            preload="metadata"
            muted
            playsInline
            onError={() => setFailed(true)}
            aria-label={`${material.title} 영상 미리보기`}
          />
          <span className="material-preview-play" aria-hidden="true">
            ▶
          </span>
        </>
      ) : (
        <img
          className="material-preview"
          src={material.file_url}
          alt={`${material.title} 이미지 미리보기`}
          loading="lazy"
          onError={() => setFailed(true)}
        />
      )}
    </a>
  )
}

export default function MaterialsPage() {
  const [materials, setMaterials] = useState([])
  const [loadError, setLoadError] = useState('')
  const [isLoading, setIsLoading] = useState(true)

  const [title, setTitle] = useState('')
  const [memo, setMemo] = useState('')
  const [file, setFile] = useState(null)
  const [errors, setErrors] = useState({})
  const [formError, setFormError] = useState('')
  const [notice, setNotice] = useState('')
  const [isUploading, setIsUploading] = useState(false)
  const fileInput = useRef(null)

  const [deleteError, setDeleteError] = useState('')

  useEffect(() => {
    let ignore = false
    listMaterials().then((result) => {
      if (ignore) return
      setIsLoading(false)
      if (result.ok) setMaterials(result.data)
      else setLoadError(errorMessage(result))
    })
    return () => {
      ignore = true
    }
  }, [])

  function chooseFile(event) {
    const chosen = event.target.files[0] ?? null
    setFile(chosen)
    setErrors((current) => ({ ...current, file: chosen ? fileError(chosen) : '' }))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    const trimmedTitle = title.trim()
    const checks = {
      title:
        trimmedTitle === ''
          ? '제목을 입력해 주세요.'
          : length(trimmedTitle) > TITLE_MAX
            ? `제목은 1~${TITLE_MAX}자로 입력해 주세요.`
            : '',
      memo: length(memo.trim()) > MEMO_MAX ? `메모는 ${MEMO_MAX.toLocaleString()}자 이하로 입력해 주세요.` : '',
      file: fileError(file),
    }
    setNotice('')
    setFormError('')
    setErrors(checks)
    if (Object.values(checks).some(Boolean)) return

    setIsUploading(true)
    const result = await uploadMaterial(title, memo, file)
    setIsUploading(false)

    if (!result.ok) {
      // Keep what was typed and chosen, and say why.
      setErrors(fieldErrors(result))
      setFormError(errorMessage(result))
      return
    }
    setMaterials((current) => [result.data, ...current])
    setTitle('')
    setMemo('')
    setFile(null)
    setErrors({})
    if (fileInput.current) fileInput.current.value = ''
    setNotice(result.data.ai_status === 'done' ? '자료를 저장하고 AI 요약을 만들었습니다.' : '자료를 저장했습니다.')
  }

  async function handleDelete(material) {
    if (!window.confirm(`"${material.title}" 자료를 삭제할까요? 원본 파일도 함께 지워집니다.`)) return
    const result = await deleteMaterial(material.id)
    if (!result.ok) {
      setDeleteError(errorMessage(result))
      return
    }
    setDeleteError('')
    setMaterials((current) => current.filter((item) => item.id !== material.id))
  }

  const rule = file ? fileRule(file) : undefined

  return (
    <div className="materials">
      <header className="materials-heading">
        <div>
          <span className="materials-eyebrow">LEARNING LIBRARY</span>
          <h1>학습 자료함</h1>
          <p>다시 보고 싶은 이미지와 영상을 나만 볼 수 있게 모아두세요. 올리면 AI가 내용을 요약해 줍니다.</p>
        </div>
        <span className="materials-badge">{materials.length}개</span>
      </header>

      <div className="materials-layout">
        <section className="materials-panel" aria-labelledby="materials-form-title">
          <span className="materials-step">NEW MATERIAL</span>
          <h2 id="materials-form-title">자료 등록</h2>

          <form className="materials-form" onSubmit={handleSubmit} noValidate>
            <div className="field">
              <label htmlFor="material-title">제목 (1~{TITLE_MAX}자)</label>
              <input
                id="material-title"
                value={title}
                onChange={(event) => setTitle(event.target.value)}
                placeholder="자료 제목을 입력하세요"
                aria-invalid={errors.title ? 'true' : undefined}
                aria-describedby={errors.title ? 'material-title-error' : undefined}
              />
              {errors.title && (
                <p id="material-title-error" className="field-error">
                  {errors.title}
                </p>
              )}
            </div>

            <div className="field">
              <label htmlFor="material-memo">메모 (선택, {MEMO_MAX.toLocaleString()}자 이하)</label>
              <textarea
                id="material-memo"
                value={memo}
                onChange={(event) => setMemo(event.target.value)}
                placeholder="나중에 다시 볼 내용을 적어두세요"
                rows="4"
                aria-invalid={errors.memo ? 'true' : undefined}
                aria-describedby="material-memo-count"
              />
              <p id="material-memo-count" className="materials-count">
                {length(memo.trim()).toLocaleString()} / {MEMO_MAX.toLocaleString()}자
              </p>
              {errors.memo && <p className="field-error">{errors.memo}</p>}
            </div>

            <div className="field">
              <label htmlFor="material-file">파일 (PNG·JPG 5MB, MP4 30MB까지 한 개)</label>
              <input
                id="material-file"
                ref={fileInput}
                type="file"
                accept={ACCEPT}
                onChange={chooseFile}
                aria-invalid={errors.file ? 'true' : undefined}
                aria-describedby={errors.file ? 'material-file-error' : undefined}
              />
              {file && (
                <p className="materials-file-chosen">
                  {rule?.kind ?? '파일'} · {file.name} · {formatSize(file.size)}
                </p>
              )}
              {errors.file && (
                <p id="material-file-error" className="field-error">
                  {errors.file}
                </p>
              )}
            </div>

            {formError && !Object.values(errors).some(Boolean) && (
              <p className="alert alert-error">{formError}</p>
            )}
            {notice && <p className="alert alert-success">{notice}</p>}

            <button type="submit" className="primary materials-submit" disabled={isUploading}>
              {isUploading ? '올리고 AI 요약을 만드는 중...' : '업로드'}
            </button>
            {isUploading && <p className="muted materials-wait">영상은 요약까지 1분 가까이 걸릴 수 있습니다.</p>}
          </form>
        </section>

        <section className="materials-panel" aria-labelledby="materials-list-title">
          <span className="materials-step">YOUR LIBRARY</span>
          <h2 id="materials-list-title">모아둔 자료</h2>

          {deleteError && <p className="alert alert-error">{deleteError}</p>}
          {isLoading && <p className="muted">불러오는 중입니다.</p>}
          {loadError && <p className="alert alert-error">{loadError}</p>}
          {!isLoading && !loadError && materials.length === 0 && (
            <p className="materials-empty">아직 올린 자료가 없습니다.</p>
          )}

          <ul className="materials-list">
            {materials.map((material) => (
              <li key={material.id} className="material-item">
                <MaterialPreview material={material} />
                <div className="material-body">
                  <div className="material-title-row">
                    <h3>{material.title}</h3>
                    <time dateTime={material.created_at}>{formatDate(material.created_at)}</time>
                  </div>
                  {material.memo && <p className="material-memo">{material.memo}</p>}
                  <p className="material-file">
                    {material.original_filename} · {formatSize(material.file_size)}
                  </p>

                  <div className={`material-ai material-ai-${material.ai_status}`}>
                    <strong>AI 요약</strong>
                    <p>{material.ai_status === 'done' ? material.ai_summary : AI_MESSAGES[material.ai_status]}</p>
                  </div>

                  <div className="material-actions">
                    <a href={material.file_url} target="_blank" rel="noreferrer">
                      원본 보기
                    </a>
                    <button type="button" className="link-button material-delete" onClick={() => handleDelete(material)}>
                      삭제
                    </button>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  )
}
