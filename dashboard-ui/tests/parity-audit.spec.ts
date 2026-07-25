import { test, expect } from '@playwright/test';
import fs from 'fs';
import path from 'path';

// Helper to log in through the UI
const realLogin = async (page: any) => {
  await page.goto('/dashboard/login');
  await page.getByPlaceholder('sk_...').fill('sk_demo_key_123'); // Ensure this matches actual demo key or setup
  await page.getByRole('button', { name: 'Login' }).click();
  await expect(page).not.toHaveURL(/.*\/login/);
};

test.describe('Mercury Dashboard V1 E2E Verification', () => {
  test('Workflow A - First Run', async ({ page, context }) => {
    await realLogin(page);
    
    await page.getByRole('link', { name: 'Overview' }).click();
    try {
      // Wait for it to become visible with a longer timeout
      await expect(page.getByText('Total Queries')).toBeVisible({ timeout: 10000 });
      await expect(page.getByText('Avg Latency')).toBeVisible();
      await expect(page.getByText('Zero Results')).toBeVisible();
    } catch (e) {
      await page.screenshot({ path: 'test-results/dashboard-failure.png' });
      throw e;
    }
  });

  test('Workflow B & C - Ingestion and Catalog', async ({ page, context }) => {
    await realLogin(page);
    
    // 1. Create a dummy CSV file
    const csvContent = `id,name,price,description\nTEST01,Playwright Product,99.99,E2E test product`;
    const tempFilePath = path.join(process.cwd(), 'tests', 'test-catalog.csv');
    
    // Ensure dir exists
    if (!fs.existsSync(path.join(process.cwd(), 'tests'))) {
      fs.mkdirSync(path.join(process.cwd(), 'tests'));
    }
    fs.writeFileSync(tempFilePath, csvContent);

    try {
      // 2. Go to ingest flow
      await page.getByRole('link', { name: 'Ingest' }).click();
      await page.getByRole('button', { name: 'File Upload CSV or JSON files' }).click();
      await page.getByRole('button', { name: 'Continue to Configuration' }).click();

      // 3. Upload file
      await page.setInputFiles('input[type="file"]', tempFilePath);
      
      // 4. Mapping step
      await expect(page.getByText('Strict Mapping Mode')).toBeVisible({ timeout: 10000 });
      await page.getByRole('button', { name: 'Start Ingestion' }).click();

      // 5. Progress and Completion
      await expect(page.getByText('Ingestion Complete')).toBeVisible({ timeout: 15000 });
      
      // 6. Navigate to Catalog
      await page.getByRole('button', { name: 'View Catalog' }).click();
      
      // 7. Verify product is in Catalog
      await expect(page.getByText('Playwright Product')).toBeVisible({ timeout: 10000 });
    } catch (e) {
      await page.screenshot({ path: 'test-results/ingest-failure.png' });
      throw e;
    } finally {
      // Clean up
      if (fs.existsSync(tempFilePath)) {
        fs.unlinkSync(tempFilePath);
      }
    }
  });
});
