import { render, screen } from '@testing-library/react';
import { TextArea } from './TextArea';
import { describe, it, expect } from 'vitest';

describe('TextArea Component', () => {
  it('renders correctly', () => {
    // Satisfy TypeScript by providing label, even if optional in some versions
    render(<TextArea label="" placeholder="Enter text" />);
    const textarea = screen.getByPlaceholderText('Enter text');
    expect(textarea).toBeInTheDocument();
  });

  it('renders correctly with a label', () => {
    render(<TextArea label="My Label" id="my-textarea" />);
    expect(screen.getByText('My Label')).toBeInTheDocument();

    // Check if textarea is present
    const textarea = document.querySelector('textarea');
    expect(textarea).toBeInTheDocument();
  });

  it('passes through className properly', () => {
    render(<TextArea label="Class Test" className="custom-class" data-testid="test-textarea" />);
    const textarea = screen.getByTestId('test-textarea');
    expect(textarea.className).toContain('custom-class');
  });

  it('passes standard HTML props like placeholder and disabled', () => {
    render(<TextArea label="Props Test" placeholder="Test Placeholder" disabled data-testid="test-textarea" />);
    const textarea = screen.getByTestId('test-textarea');
    expect(textarea).toHaveAttribute('placeholder', 'Test Placeholder');
    expect(textarea).toBeDisabled();
  });
});
