import { useEffect, useState } from 'react'
import './App.css'

function App() {
  const [health, setHealth] = useState({ state: 'loading' })

  useEffect(() => {
    fetch('/api/health')
      .then((response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`)
        return response.json()
      })
      .then((data) => setHealth({ state: 'ok', message: data.message }))
      .catch(() => setHealth({ state: 'error' }))
  }, [])

  return (
    <main className="app">
      <h1>BuildLog</h1>
      <p className={`status status-${health.state}`}>
        {health.state === 'loading' && '서버 상태를 확인하는 중입니다.'}
        {health.state === 'ok' && health.message}
        {health.state === 'error' && '서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해 주세요.'}
      </p>
    </main>
  )
}

export default App
