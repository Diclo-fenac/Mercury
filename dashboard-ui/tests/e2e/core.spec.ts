import { test, expect } from '@playwright/test';

// Helper to log in through the UI
const realLogin = async (page: any) => {
  await page.goto('/dashboard/login');
  await page.getByPlaceholder('sk_...').fill('sk_demo_key_123'); // Ensure this matches actual demo key or setup
  await page.getByRole('button', { name: 'Login' }).click();
  // Wait for redirect to dashboard index or catalog
  await expect(page).not.toHaveURL(/.*\/login/);
};

test.describe('Mercury Core Workflows', () => {
  
  test('1. Authentication and Protected Routes', async ({ page, context }) => {
    // Attempt to visit protected route
    await page.goto('/dashboard/catalog');
    
    // Should redirect to login
    await expect(page).toHaveURL(/.*\/login/);
    await expect(page.getByText('Login to Mercury')).toBeVisible();

    // Login with fake admin key
    await page.getByPlaceholder('sk_...').fill('sk_demo_key_123');
    
    // Click login
    await page.getByRole('button', { name: 'Login' }).click();

    // Verify successful redirect to the dashboard
    await expect(page).not.toHaveURL(/.*\/login/);
  });

  test('5. Search Query, Debounce, and Pagination', async ({ page, context }) => {
    await realLogin(page);

    // Mock search API
    await page.route('**/api/v1/search', route => {
      route.fulfill({
        status: 200,
        json: {
          results: [
            { id: '1', title: 'Test Product', price: 99.99, status: 'active' }
          ],
          total_results: 1,
          page: 1
        }
      });
    });

    await page.goto('/dashboard/catalog');
    
    // Ensure table loads
    await expect(page.getByText('Product Catalog')).toBeVisible();
    
    // Test search debounce
    const searchInput = page.getByPlaceholder('Search products...');
    await searchInput.fill('Test');
    
    // Wait for debounce and row to appear
    await expect(page.getByText('Test Product')).toBeVisible();
  });

  test('7. Merchandising pin/hide rule creation', async ({ page, context }) => {
    await realLogin(page);

    // Let it hit the real backend
    // Navigate via sidebar
    await page.getByRole('link', { name: 'Merchandising' }).click();
    
    await page.getByPlaceholder('e.g. running shoes').fill('shoes');
    await page.getByPlaceholder('e.g. prod_12345').fill('prod_999');
    
    await page.getByRole('button', { name: 'Pin Product' }).click();
    
    // Check toast success
    await expect(page.getByText('Product pinned successfully')).toBeVisible();
  });

  test('8. Public widget key generation', async ({ page, context }) => {
    await realLogin(page);

    // Mock keys response
    await page.route('**/api/v1/admin/keys', route => {
      route.fulfill({
        status: 200,
        json: [
          { id: '1', prefix: 'pk_abc123', type: 'public_search', name: 'Widget Key' }
        ]
      });
    });

    // Navigate via sidebar
    await page.getByRole('link', { name: 'Go Live' }).click();
    
    await expect(page.getByText('Go Live')).toBeVisible();
    
    // Verify snippet contains the public key
    const snippet = page.locator('pre');
    await expect(snippet).toContainText('pk_abc123');
  });

});
