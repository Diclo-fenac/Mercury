import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Home } from './pages/Home'
import { Search } from './pages/Search'
import { ProductDetail } from './pages/ProductDetail'
import { Chat } from './pages/Chat'
import { Conversations } from './pages/Conversations'
import { Images } from './pages/Images'
import { Profile } from './pages/Profile'
import { Login } from './pages/Login'
import { Header } from './components/layout/Header'
import { Footer } from './components/layout/Footer'
import { ToastContainer } from './components/ui/Toast'

import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        <Header />
        <main className="container mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/search" element={<Search />} />
            <Route path="/product/:id" element={<ProductDetail />} />
            <Route path="/chat" element={<Chat />} />
            <Route path="/conversations" element={<Conversations />} />
            <Route path="/images" element={<Images />} />
            <Route path="/profile" element={<Profile />} />
            <Route path="/login" element={<Login />} />
          </Routes>
        </main>
        <Footer />
        <ToastContainer />
      </div>
    </BrowserRouter>
  </React.StrictMode>,
)
