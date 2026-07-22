import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import AdminAiFundDashboard from '../pages/AdminAiFundDashboard'

describe('AdminAiFundDashboard Component', () => {
  it('renders Admin AI Fund Emergency Kill-Switch button', () => {
    render(<AdminAiFundDashboard userId="test-admin-id" />)
    const killSwitchBtn = screen.getByRole('button', { name: /Emergency Stop/i })
    expect(killSwitchBtn).toBeInTheDocument()
  })
})
