import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from '../supabaseClient'

export default function Login() {
  const navigate = useNavigate()

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session) navigate('/')
    })
  }, [navigate])

  const handleKakaoLogin = async () => {
    try {
      const { error } = await supabase.auth.signInWithOAuth({
        provider: 'kakao',
        options: {
          redirectTo: `${window.location.origin}/`,
          queryParams: {
            scope: 'account_email',
            prompt: 'login',
          },
        },
      })
      if (error) throw error
    } catch (error) {
      alert(`카카오 로그인 실패: ${error.message}`)
    }
  }

  return (
    <div className="relative flex min-h-screen overflow-hidden bg-[#11131a] font-inter text-[#e2e2ec]">
      <div className="z-10 flex w-full flex-col justify-center bg-[#0c0e15] px-6 py-10 shadow-[8px_0_24px_rgba(0,0,0,0.5)] lg:w-5/12">
        <div className="mx-auto w-full max-w-md">
          <div className="mb-12">
            <div className="mb-2 flex items-center gap-3">
              <img src="/logo.png" alt="Logo" className="h-8 w-8 object-contain" />
              <h1 className="text-xl font-bold tracking-wider text-primary">ANTRY</h1>
            </div>
            <p className="text-sm text-slate-400">ANTRY에 오신 것을 환영합니다.</p>
          </div>

          <button
            className="flex w-full items-center justify-center gap-3 rounded bg-[#FEE500] py-3 text-sm font-semibold text-[#191919] shadow-sm transition-colors hover:bg-[#FADA0A]"
            type="button"
            onClick={handleKakaoLogin}
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="18" height="30" className="h-[30px] w-[18px]">
              <path fill="#191919" d="M12 3c-4.97 0-9 3.185-9 7.11 0 2.507 1.657 4.702 4.14 5.86l-.81 2.977c-.086.315.228.583.513.395l3.522-2.31c.214.025.43.038.647.038 4.97 0 9-3.186 9-7.11C21 6.185 16.97 3 12 3z" />
            </svg>
            <span>카카오 로그인</span>
          </button>

          <div className="mt-6 text-center">
            <button
              type="button"
              onClick={() => navigate('/')}
              className="text-xs text-slate-500 underline transition-colors hover:text-slate-300"
            >
              ← 홈으로 돌아가기
            </button>
          </div>
        </div>
      </div>

      <div className="relative hidden w-7/12 overflow-hidden bg-[#1d1f27] lg:block">
        <div className="absolute inset-0 z-10 w-32 bg-gradient-to-r from-[#0c0e15] to-transparent" />
        <div
          className="absolute inset-0 h-full w-full scale-[1.1] animate-[spin_180s_linear_infinite] bg-cover bg-center opacity-40 mix-blend-screen"
          style={{ backgroundImage: "url('https://lh3.googleusercontent.com/aida-public/AB6AXuApLxgfDjYyQecXJZuWNXU9Ga_b7gYY3LPueCaxOazI8GjN9-RO0LWVrVv7c7sp6cBStFrPAWkr9-CSXMBCaIeUFGuwrKINONZTSbMklhQNkkUqTXSVcQctVEG5h3WMCb5gEGhygwwyk54ai7IDnqpk6FWQ7Zub8IV6OpayDku7z1TcG4f-c6Fb2k28tAyhbifVOFUdg195Z1r9H5Hra-t3ZQcY33i0X-18iU3i-igI384E5nJdCSKyMVw6WkLYNHbGZxsBTIJ3mTE')" }}
        />
      </div>
    </div>
  )
}
