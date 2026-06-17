import { render, screen } from '@testing-library/react';
import { Button } from './Button';
import { describe, it, expect } from 'vitest';

describe('Button Component', () => {
  it('renders children correctly', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole('button', { name: 'Click me' })).toBeInTheDocument();
  });

  it('is disabled and shows spinner when isLoading is true', () => {
    const { container } = render(<Button isLoading>Click me</Button>);
    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
    expect(screen.queryByText('Click me')).not.toBeInTheDocument();
    expect(container.querySelector('.animate-spin')).toBeInTheDocument();
  });

  it('is disabled when disabled prop is provided', () => {
    render(<Button disabled>Click me</Button>);
    expect(screen.getByRole('button', { name: 'Click me' })).toBeDisabled();
  });

  it('applies primary variant classes by default', () => {
    render(<Button>Click me</Button>);
    const button = screen.getByRole('button', { name: 'Click me' });
    expect(button.className).toContain('bg-rose-400');
  });

  it('applies secondary variant classes when provided', () => {
    render(<Button variant="secondary">Click me</Button>);
    const button = screen.getByRole('button', { name: 'Click me' });
    expect(button.className).toContain('bg-white');
  });
});
