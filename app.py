import streamlit as st
import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import pandas as pd
import io
import os

# 1. Setup & Install Browsers (Runs once on app start)
@st.cache_resource
def install_browsers():
    # Installs chromium and the system dependencies it needs
    os.system("playwright install chromium")
    os.system("playwright install-deps chromium")

install_browsers()

async def run_scraper(url, limit):
    # 2. Use Stealth with Playwright
    # The 'Stealth().use_async' wrapper applies evasions to all pages created
    async with Stealth().use_async(async_playwright()) as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        
        # Create a context (like a browser session)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        
        page = await context.new_page()
        results = []

        try:
            st.info(f"Navigating to category...")
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            # Extract product links
            links = await page.eval_on_selector_all(
                "a.product-card__name", 
                "elements => elements.map(e => e.href)"
            )
            
            links_to_scrape = links[:limit]
            progress_bar = st.progress(0)

            for i, link in enumerate(links_to_scrape):
                await page.goto(link, wait_until="networkidle")
                
                # Simple extraction example
                # Note: You'll replace this with the JSON-LD logic from before
                product_name = await page.title()
                
                results.append({
                    "Variant Name": product_name,
                    "URL": link,
                    "Status": "Success"
                })
                
                progress_bar.progress((i + 1) / len(links_to_scrape))
                
        except Exception as e:
            st.error(f"Scraping error: {e}")
        finally:
            await browser.close()
            
        return pd.DataFrame(results)

# --- Streamlit UI ---
st.title("🛡️ Stealth Auchan Scraper")
target_url = st.text_input("Category URL", "https://zakupy.auchan.pl/categories/higiena-i-kosmetyki/kosmetyki-do-piel%C4%99gnacji/3847")
num_items = st.number_input("Items to scrape", min_value=1, max_value=100, value=5)

if st.button("Run Scraper"):
    df_results = asyncio.run(run_scraper(target_url, num_items))
    
    if not df_results.empty:
        st.write(df_results)
        
        # Excel Export
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_results.to_excel(writer, index=False)
        
        st.download_button(
            label="Download Excel Results",
            data=buffer.getvalue(),
            file_name="auchan_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
