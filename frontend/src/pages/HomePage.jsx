import { useAuth } from '../auth/context.js'
import './HomePage.css'

// Layout follows the Figma dashboard (node 2:12). The cards stay empty until the records
// exist; Phase 12 fills them with 3 recent study logs, 5 open todos and 3 unsolved errors.
const panels = [
  { key: 'recent', title: '최근 공부 기록', empty: '아직 공부 기록이 없습니다.' },
  { key: 'todos', title: '남은 할 일', empty: '아직 남은 할 일이 없습니다.' },
  { key: 'errors', title: '미해결 오류', empty: '아직 미해결 오류가 없습니다.' },
]

export default function HomePage() {
  const { user } = useAuth()

  return (
    <div className="home">
      <p className="home-eyebrow">내 학습 한눈에 보기</p>

      <header className="home-greeting">
        <h1>{user.nickname}님, 차곡차곡 쌓이고 있어요</h1>
        <p>오늘의 배움도 기록으로 남겨보세요.</p>
      </header>

      <div className="home-grid">
        {panels.map((panel) => (
          <section key={panel.key} className={`home-panel home-panel-${panel.key}`}>
            <h2>{panel.title}</h2>
            <p className="home-empty">{panel.empty}</p>
          </section>
        ))}
      </div>
    </div>
  )
}
