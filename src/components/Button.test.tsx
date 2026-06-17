import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Button } from './Button';

describe('Button', () => {
  it('renders children when not loading', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeDefined();
    expect(screen.queryByTestId('button-spinner')).toBeNull();
  });

  it('renders spinner and hides children when isLoading is true', () => {
    render(<Button isLoading>Click me</Button>);
    expect(screen.queryByText('Click me')).toBeNull();
    expect(screen.getByTestId('button-spinner')).toBeDefined();
  });

  it('is disabled when isLoading is true', () => {
    render(<Button isLoading>Click me</Button>);
    const button = screen.getByRole('button');
    expect(button.hasAttribute('disabled')).toBe(true);
  });

  it('has aria-busy attribute when isLoading is true', () => {
    render(<Button isLoading>Click me</Button>);
    const button = screen.getByRole('button');
    expect(button.getAttribute('aria-busy')).toBe('true');
  });

  it('is disabled when disabled prop is true', () => {
    render(<Button disabled>Click me</Button>);
    const button = screen.getByRole('button');
    expect(button.hasAttribute('disabled')).toBe(true);
  });
});
