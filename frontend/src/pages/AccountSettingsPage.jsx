import { useState } from 'react'
import { changeNickname } from '../api/auth.js'
import { errorMessage, fieldErrors } from '../api/client.js'
import { useAuth } from '../auth/context.js'
import FormField from '../components/FormField.jsx'

export default function AccountSettingsPage() {
  const { user, setUser } = useAuth()
  const [nickname, setNickname] = useState(user.nickname)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    setIsSubmitting(true)
    const result = await changeNickname(nickname)
    setIsSubmitting(false)

    if (result.ok) {
      setUser(result.data)
      setNickname(result.data.nickname)
      setError('')
      setNotice('닉네임을 변경했습니다.')
      return
    }
    // spec 2.3: keep what was typed and say why.
    setNotice('')
    setError(fieldErrors(result).nickname ?? errorMessage(result))
  }

  return (
    <section className="card narrow">
      <h1>계정 설정</h1>
      <dl className="account-info">
        <dt>이메일</dt>
        <dd>{user.email}</dd>
        <dt>현재 닉네임</dt>
        <dd>{user.nickname}</dd>
      </dl>
      <form onSubmit={handleSubmit} noValidate>
        <FormField
          id="nickname"
          label="새 닉네임 (2~20자, 한글·영문·숫자·밑줄)"
          value={nickname}
          onChange={setNickname}
          error={error}
          autoComplete="nickname"
        />
        {notice && <p className="alert alert-success">{notice}</p>}
        <button type="submit" className="primary" disabled={isSubmitting}>
          {isSubmitting ? '변경하는 중...' : '닉네임 변경'}
        </button>
      </form>
    </section>
  )
}
