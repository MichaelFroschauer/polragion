import { useEffect, useState } from 'react'
import { healthApi } from './api/client'
import './App.css'
import Page from "@/Page.tsx";

function App() {
  // const [count, setCount] = useState(0)
  // const [health, setHealth] = useState<string>('checking…')

  // useEffect(() => {
  //   healthApi
  //     .liveness()
  //     .then((res) => setHealth(res.status))
  //     .catch(() => setHealth('unreachable'))
  // }, [])

  return (
    <>
      <Page></Page>
    </>
  )
}

export default App
