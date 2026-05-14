import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation } from '@tanstack/react-query'

import { api, ApiError } from '@/lib/api'
import { useAuth } from '@/lib/auth-context'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

const schema = z.object({
  full_name: z.string().min(1, 'Name is required').max(200),
  email: z.string().email({ message: 'Enter a valid email address' }),
})

type FormValues = z.infer<typeof schema>

export function ProfileSection() {
  const { user, updateUser } = useAuth()
  const [successMessage, setSuccessMessage] = useState('')

  const {
    register,
    handleSubmit,
    reset,
    setError,
    formState: { errors, isDirty, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { full_name: user?.full_name ?? '', email: user?.email ?? '' },
  })

  // Keep form in sync if auth context user changes externally
  useEffect(() => {
    if (user) reset({ full_name: user.full_name, email: user.email })
  }, [user, reset])

  const mutation = useMutation({
    mutationFn: (values: FormValues) => api.auth.updateMe(values),
    onSuccess: (updated) => {
      updateUser(updated)
      reset({ full_name: updated.full_name, email: updated.email })
      setSuccessMessage('Profile updated')
      setTimeout(() => setSuccessMessage(''), 2000)
    },
    onError: (err) => {
      if (err instanceof ApiError && err.status === 409) {
        setError('email', { message: 'That email is already in use' })
      }
    },
  })

  return (
    <Card>
      <CardContent className="p-6">
        <h2 className="font-serif text-xl mb-4">Profile</h2>
        <form onSubmit={handleSubmit((v) => mutation.mutate(v))} className="space-y-4 max-w-sm">
          <div className="space-y-1">
            <Label htmlFor="full_name">Full name</Label>
            <Input id="full_name" {...register('full_name')} />
            {errors.full_name && (
              <p className="text-xs text-red-600">{errors.full_name.message}</p>
            )}
          </div>

          <div className="space-y-1">
            <Label htmlFor="email">Email</Label>
            <Input id="email" type="email" {...register('email')} />
            {errors.email && (
              <p className="text-xs text-red-600">{errors.email.message}</p>
            )}
          </div>

          {mutation.error && !(mutation.error instanceof ApiError && mutation.error.status === 409) && (
            <p className="text-xs text-red-600">Something went wrong. Please try again.</p>
          )}

          {successMessage && (
            <p className="text-xs text-green-600">{successMessage}</p>
          )}

          <Button type="submit" disabled={!isDirty || isSubmitting}>
            {isSubmitting ? 'Saving…' : 'Save changes'}
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}
