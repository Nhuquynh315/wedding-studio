import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useNavigate, useLocation } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { ApiError } from '@/lib/api'
import { useAuth } from '@/lib/auth-context'
import { loginSchema, type LoginFormValues } from '@/pages/loginSchema'

export function LoginPage() {
  const { user, isLoading, login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [submitError, setSubmitError] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: '', password: '' },
  })

  const fromPath = (location.state as { from?: string })?.from || '/'
  useEffect(() => {
    if (!isLoading && user) {
      navigate(fromPath, { replace: true })
    }
  }, [isLoading, user, navigate, fromPath])

  const onSubmit = async (values: LoginFormValues) => {
    setSubmitError(null)
    try {
      await login(values.email, values.password)
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 401) {
          setSubmitError('Incorrect email or password.')
        } else if (err.status === 422) {
          setSubmitError('Please check your input.')
        } else {
          setSubmitError(err.problem.title || 'Something went wrong.')
        }
      } else {
        setSubmitError('Network error. Please try again.')
      }
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="font-serif text-5xl mb-2 text-[var(--color-text-dark)]">
            Wedding Studio
          </h1>
          <p className="text-sm tracking-widest uppercase text-[var(--color-rose)]">
            Welcome back
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="font-serif text-2xl text-center">Log in</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  autoComplete="email"
                  autoFocus
                  {...register('email')}
                  aria-invalid={!!errors.email}
                />
                {errors.email && (
                  <p className="text-sm text-red-600">{errors.email.message}</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  autoComplete="current-password"
                  {...register('password')}
                  aria-invalid={!!errors.password}
                />
                {errors.password && (
                  <p className="text-sm text-red-600">{errors.password.message}</p>
                )}
              </div>

              {submitError && (
                <div
                  role="alert"
                  className="text-sm text-red-700 bg-red-50 border border-red-200 rounded p-2"
                >
                  {submitError}
                </div>
              )}

              <Button
                type="submit"
                disabled={isSubmitting}
                className="w-full bg-[var(--color-rose)] hover:bg-[var(--color-rose-dark)] text-white"
              >
                {isSubmitting ? 'Logging in…' : 'Log in'}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
