import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation } from '@tanstack/react-query'

import { api, ApiError } from '@/lib/api'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

const schema = z
  .object({
    current_password: z.string().min(1, 'Current password is required'),
    new_password: z.string().min(8, 'At least 8 characters').max(128),
    confirm_new_password: z.string(),
  })
  .refine((d) => d.new_password === d.confirm_new_password, {
    message: 'Passwords do not match',
    path: ['confirm_new_password'],
  })

type FormValues = z.infer<typeof schema>

export function PasswordSection() {
  const [successMessage, setSuccessMessage] = useState('')

  const {
    register,
    handleSubmit,
    reset,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) })

  const mutation = useMutation({
    mutationFn: ({ current_password, new_password }: FormValues) =>
      api.auth.changePassword({ current_password, new_password }),
    onSuccess: () => {
      reset()
      setSuccessMessage('Password updated')
      setTimeout(() => setSuccessMessage(''), 2000)
    },
    onError: (err) => {
      if (err instanceof ApiError && err.status === 400) {
        setError('current_password', { message: 'Current password is incorrect' })
      }
    },
  })

  return (
    <Card>
      <CardContent className="p-6">
        <h2 className="font-serif text-xl mb-4">Change password</h2>
        <form onSubmit={handleSubmit((v) => mutation.mutate(v))} className="space-y-4 max-w-sm">
          <div className="space-y-1">
            <Label htmlFor="current_password">Current password</Label>
            <Input id="current_password" type="password" {...register('current_password')} />
            {errors.current_password && (
              <p className="text-xs text-red-600">{errors.current_password.message}</p>
            )}
          </div>

          <div className="space-y-1">
            <Label htmlFor="new_password">New password</Label>
            <Input id="new_password" type="password" {...register('new_password')} />
            {errors.new_password && (
              <p className="text-xs text-red-600">{errors.new_password.message}</p>
            )}
          </div>

          <div className="space-y-1">
            <Label htmlFor="confirm_new_password">Confirm new password</Label>
            <Input id="confirm_new_password" type="password" {...register('confirm_new_password')} />
            {errors.confirm_new_password && (
              <p className="text-xs text-red-600">{errors.confirm_new_password.message}</p>
            )}
          </div>

          {mutation.error && !(mutation.error instanceof ApiError && mutation.error.status === 400) && (
            <p className="text-xs text-red-600">Something went wrong. Please try again.</p>
          )}

          {successMessage && (
            <p className="text-xs text-green-600">{successMessage}</p>
          )}

          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Saving…' : 'Update password'}
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}
