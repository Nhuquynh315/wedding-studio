import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { ApiError, api } from '@/lib/api'
import { useAuth } from '@/lib/auth-context'
import { registerSchema, type RegisterFormValues } from '@/pages/registerSchema'

export function RegisterPage() {
  const { user, isLoading, login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [submitError, setSubmitError] = useState<string | null>(null)

  const {
    register: registerField,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      full_name: '',
      email: '',
      password: '',
      confirm_password: '',
    },
  })

  const fromPath = (location.state as { from?: string })?.from || '/'
  useEffect(() => {
    if (!isLoading && user) {
      navigate(fromPath, { replace: true })
    }
  }, [isLoading, user, navigate, fromPath])

  const onSubmit = async (values: RegisterFormValues) => {
    setSubmitError(null)
    try {
      await api.auth.register({
        full_name: values.full_name,
        email: values.email,
        password: values.password,
      })
      await login(values.email, values.password)
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 409) {
          setSubmitError(
            'An account with this email already exists. Try logging in instead.',
          )
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
    <div className="min-h-screen flex items-center justify-center px-4 py-8">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="font-serif text-5xl mb-2 text-[var(--color-text-dark)]">
            Wedding Studio
          </h1>
          <p className="text-sm tracking-widest uppercase text-[var(--color-rose)]">
            Create your account
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="font-serif text-2xl text-center">Sign up</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="full_name">Name</Label>
                <Input
                  id="full_name"
                  type="text"
                  autoComplete="name"
                  autoFocus
                  {...registerField('full_name')}
                  aria-invalid={!!errors.full_name}
                />
                {errors.full_name && (
                  <p className="text-sm text-red-600">{errors.full_name.message}</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  autoComplete="email"
                  {...registerField('email')}
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
                  autoComplete="new-password"
                  {...registerField('password')}
                  aria-invalid={!!errors.password}
                />
                {errors.password && (
                  <p className="text-sm text-red-600">{errors.password.message}</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="confirm_password">Confirm password</Label>
                <Input
                  id="confirm_password"
                  type="password"
                  autoComplete="new-password"
                  {...registerField('confirm_password')}
                  aria-invalid={!!errors.confirm_password}
                />
                {errors.confirm_password && (
                  <p className="text-sm text-red-600">{errors.confirm_password.message}</p>
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
                {isSubmitting ? 'Creating account…' : 'Sign up'}
              </Button>

              <p className="text-sm text-center text-[var(--color-text-muted)]">
                Already have an account?{' '}
                <Link
                  to="/login"
                  className="text-[var(--color-rose)] hover:underline font-medium"
                >
                  Log in
                </Link>
              </p>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
