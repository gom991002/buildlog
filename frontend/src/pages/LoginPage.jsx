import { useState } from 'react'
import { Link, useNavigate } from 'react-router'
import { login } from '../api/auth.js'
import { errorMessage } from '../api/client.js'
import { useAuth } from '../auth/context.js'
import FormField from '../components/FormField.jsx'

export default function LoginPage() {
  const navigate = useNavigate()
  const { setUser } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [message, setMessage] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    setIsSubmitting(true)
    const result = await login(email, password)
    setIsSubmitting(false)

    if (result.ok) {
      setUser(result.data)
      navigate('/', { replace: true })
      return
    }
    // spec 2.2: keep the email, clear only the password.
    setPassword('')
    setMessage(errorMessage(result))
  }

  return (
    <section className="card narrow">
      <h1>로그인</h1>
      <form onSubmit={handleSubmit} noValidate>
        <FormField id="email" label="이메일" type="email" value={email} onChange={setEmail} autoComplete="email" />
        <FormField
          id="password"
          label="비밀번호"
          type="password"
          value={password}
          onChange={setPassword}
          autoComplete="current-password"
        />
        {message && <p className="alert alert-error">{message}</p>}
        <button type="submit" className="primary" disabled={isSubmitting}>
          {isSubmitting ? '로그인하는 중...' : '로그인'}
        </button>
      </form>
      <p className="muted">
        계정이 없나요? <Link to="/signup">회원가입</Link>
      </p>
    </section>
  )
}
