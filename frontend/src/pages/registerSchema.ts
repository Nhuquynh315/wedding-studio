import { z } from 'zod'

export const registerSchema = z
  .object({
    full_name: z.string().min(1, 'Name is required').max(100, 'Name is too long'),
    email: z.string().min(1, 'Email is required').email('Please enter a valid email'),
    password: z.string().min(8, 'Password must be at least 8 characters'),
    confirm_password: z.string().min(1, 'Please confirm your password'),
  })
  .refine((data) => data.password === data.confirm_password, {
    message: "Passwords don't match",
    path: ['confirm_password'],
  })

export type RegisterFormValues = z.infer<typeof registerSchema>
