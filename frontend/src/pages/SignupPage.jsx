import { useState } from 'react'
import { Link, useNavigate } from 'react-router'
import { signup } from '../api/auth.js'
import { errorMessage, fieldErrors } from '../api/client.js'
import FormField from '../components/FormField.jsx'

export default function SignupPage() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [nickname, setNickname] = useState('')
  const [errors, setErrors] = useState({})
  const [message, setMessage] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    setIsSubmitting(true)
    const result = await signup(email, password, nickname)
    setIsSubmitting(false)

    if (result.ok) {
      navigate('/login', { replace: true })
      return
    }
    // spec 2.1: keep the email and nickname, clear only the password.
    setPassword('')
    setErrors(fieldErrors(result))
    setMessage(errorMessage(result))
  }

  return (
    <section className="card narrow">
      <h1>회원가입</h1>
      <form onSubmit={handleSubmit} noValidate>
        <FormField id="email" label="이메일" type="email" value={email} onChange={setEmail} error={errors.email} autoComplete="email" />
        <FormField
          id="password"
          label="비밀번호 (8~64자)"
          type="password"
          value={password}
          onChange={setPassword}
          error={errors.password}
          autoComplete="new-password"
        />
        <FormField
          id="nickname"
          label="닉네임 (2~20자, 한글·영문·숫자·밑줄)"
          value={nickname}
          onChange={setNickname}
          error={errors.nickname}
          autoComplete="nickname"
        />
        {message && <p className="alert alert-error">{message}</p>}
        <button type="submit" className="primary" disabled={isSubmitting}>
          {isSubmitting ? '가입하는 중...' : '회원가입'}
        </button>
      </form>
      <p className="muted">
        이미 계정이 있나요? <Link to="/login">로그인</Link>
      </p>
    </section>
  )
}
