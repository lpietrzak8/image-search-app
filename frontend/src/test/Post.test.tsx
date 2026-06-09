import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import axios from 'axios'
import Post from '../components/Post'

vi.mock('axios', () => ({
  default: {
    post: vi.fn(),
  },
}))

const mockImg = {
  id: 'pixabay-1',
  author: { name: 'John Doe', url: 'http://example.com/john' },
  description: 'A beautiful sunset',
  keywords: ['sunset', 'nature', 'sky'],
  image_url: 'http://example.com/sunset.jpg',
  source_url: 'http://example.com/page',
  provider: 'pixabay',
}

function renderPost(overrides = {}) {
  const props = {
    img: mockImg,
    onClose: vi.fn(),
    isLoggedIn: false,
    savedPhotos: new Map<string, any>(),
    savingPhoto: null,
    handleSavePhoto: vi.fn(),
    handleDeletePhoto: vi.fn(),
    results: [],
    setResults: vi.fn(),
    ...overrides,
  }
  return render(
    <MemoryRouter>
      <Post {...props} />
    </MemoryRouter>
  )
}

describe('Post', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the image', () => {
    renderPost()
    const img = screen.getByRole('img')
    expect(img).toHaveAttribute('src', mockImg.image_url)
  })

  it('renders the author name', () => {
    renderPost()
    expect(screen.getByText(/John Doe/)).toBeInTheDocument()
  })

  it('renders all keywords', () => {
    renderPost()
    expect(screen.getByText('sunset')).toBeInTheDocument()
    expect(screen.getByText('nature')).toBeInTheDocument()
    expect(screen.getByText('sky')).toBeInTheDocument()
  })

  it('renders the description', () => {
    renderPost()
    expect(screen.getByText('A beautiful sunset')).toBeInTheDocument()
  })

  it('renders the source URL', () => {
    renderPost()
    expect(screen.getByText(mockImg.source_url)).toBeInTheDocument()
  })

  it('calls onClose when close button is clicked', () => {
    const onClose = vi.fn()
    renderPost({ onClose })
    fireEvent.click(screen.getByText('✕'))
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('calls onClose when overlay is clicked', () => {
    const onClose = vi.fn()
    renderPost({ onClose })
    const overlay = document.querySelector('.modal-overlay')
    fireEvent.click(overlay!)
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('does not close when postContainer is clicked', () => {
    const onClose = vi.fn()
    renderPost({ onClose })
    const container = document.querySelector('.postContainer')
    fireEvent.click(container!)
    expect(onClose).not.toHaveBeenCalled()
  })

  it('shows save button when logged in', () => {
    renderPost({ isLoggedIn: true })
    expect(screen.getByTitle('Save to My Resources')).toBeInTheDocument()
  })

  it('does not show save button when not logged in', () => {
    renderPost({ isLoggedIn: false })
    expect(screen.queryByTitle('Save to My Resources')).not.toBeInTheDocument()
  })

  it('shows saved state when image is already saved', () => {
    const savedPhotos = new Map().set(mockImg.source_url, mockImg)
    renderPost({ isLoggedIn: true, savedPhotos })
    expect(screen.getByTitle('Delete')).toBeInTheDocument()
    expect(screen.getByText('✓')).toBeInTheDocument()
  })

  it('calls handleSavePhoto when save button is clicked', () => {
    const handleSavePhoto = vi.fn()
    renderPost({ isLoggedIn: true, handleSavePhoto })
    fireEvent.click(screen.getByTitle('Save to My Resources'))
    expect(handleSavePhoto).toHaveBeenCalledWith(mockImg)
  })

  it('calls suspend API when flag button is clicked', async () => {
    const mockedAxios = axios as any
    mockedAxios.post.mockResolvedValueOnce({})
    renderPost()

    const flagBtn = document.querySelector('.suspendButton')!
    fireEvent.click(flagBtn)

    await waitFor(() => {
      expect(mockedAxios.post).toHaveBeenCalledWith(
        '/api/blacklist/suspend',
        expect.objectContaining({ source_url: mockImg.source_url })
      )
    })
  })

  it('shows suspend message after successful suspend', async () => {
    const mockedAxios = axios as any
    mockedAxios.post.mockResolvedValueOnce({
      data: { message: 'Post suspended' },
    })
    renderPost()

    const flagBtn = document.querySelector('.suspendButton')!
    fireEvent.click(flagBtn)

    await waitFor(() => {
      expect(screen.getByText('Post suspended')).toBeInTheDocument()
    })
  })

  it('shows error message when suspend fails', async () => {
    const mockedAxios = axios as any
    mockedAxios.post.mockRejectedValueOnce(new Error('Network error'))
    renderPost()

    const flagBtn = document.querySelector('.suspendButton')!
    fireEvent.click(flagBtn)

    await waitFor(() => {
      expect(screen.getByText('Something went wrong')).toBeInTheDocument()
    })
  })

  it('adds modal-open class to body on mount', () => {
    renderPost()
    expect(document.body.classList.contains('modal-open')).toBe(true)
  })
})
