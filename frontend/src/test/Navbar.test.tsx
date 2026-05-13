import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import Navbar from '../components/Navbar'

function renderNavbar(isLoggedIn: boolean) {
  return render(
    <MemoryRouter>
      <Navbar isLoggedIn={isLoggedIn} />
    </MemoryRouter>
  )
}

describe('Navbar', () => {
  it('renders the logo', () => {
    renderNavbar(false)
    expect(screen.getByText('PHOTO-SEARCH')).toBeInTheDocument()
  })

  it('shows Log-In link when not logged in', () => {
    renderNavbar(false)
    expect(screen.getByText('Log-In')).toBeInTheDocument()
    expect(screen.queryByText('My Account')).not.toBeInTheDocument()
  })

  it('shows My Account link when logged in', () => {
    renderNavbar(true)
    expect(screen.getByText('My Account')).toBeInTheDocument()
    expect(screen.queryByText('Log-In')).not.toBeInTheDocument()
  })

  it('always shows Home link', () => {
    renderNavbar(false)
    expect(screen.getByText('Home')).toBeInTheDocument()
  })

  it('always shows Our mission link', () => {
    renderNavbar(false)
    expect(screen.getByText('Our mission')).toBeInTheDocument()
  })

  it('always shows Contribute Data link', () => {
    renderNavbar(false)
    expect(screen.getByText('Contribute Data')).toBeInTheDocument()
  })

  it('hamburger button toggles menu open class', () => {
    renderNavbar(false)
    const hamburger = screen.getByRole('button', { name: /toggle menu/i })
    expect(hamburger).not.toHaveClass('active')
    fireEvent.click(hamburger)
    expect(hamburger).toHaveClass('active')
  })

  it('clicking hamburger twice closes the menu', () => {
    renderNavbar(false)
    const hamburger = screen.getByRole('button', { name: /toggle menu/i })
    fireEvent.click(hamburger)
    fireEvent.click(hamburger)
    expect(hamburger).not.toHaveClass('active')
  })

  it('clicking overlay closes the menu', () => {
    renderNavbar(false)
    const hamburger = screen.getByRole('button', { name: /toggle menu/i })
    fireEvent.click(hamburger)

    const overlay = document.querySelector('.menu-overlay')
    expect(overlay).not.toBeNull()
    fireEvent.click(overlay!)

    expect(hamburger).not.toHaveClass('active')
  })
})
