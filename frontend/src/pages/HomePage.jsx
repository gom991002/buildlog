import { useAuth } from '../auth/context.js'

// The cards (recent study logs, open todos, unsolved errors) arrive in Phase 12,
// once those records exist.
export default function HomePage() {
  const { user } = useAuth()

  return (
    <section className="card">
      <h1>내 기록</h1>
      <p>{user.nickname}님, 환영합니다.</p>
      <p className="muted">공부 기록, 할 일, 오류 기록은 다음 단계에서 이 화면에 추가됩니다.</p>
    </section>
  )
}
