import React, { type ReactElement } from 'react'
import { render, type RenderOptions } from '@testing-library/react'

// Wrapper for providers (if we add them later like ThemeProvider, StoreProvider context, etc.)
// Currently just a generic wrapper
const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
    return (
        <>
            {children}
        </>
    )
}

const customRender = (
    ui: ReactElement,
    options?: Omit<RenderOptions, 'wrapper'>,
) => render(ui, { wrapper: AllTheProviders, ...options })

// re-export everything
export * from '@testing-library/react'

// override render method
export { customRender as render }
