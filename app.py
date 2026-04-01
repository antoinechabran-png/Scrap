import streamlit as st
import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import io

# --- APP INTERFACE ---
st.title("Auchan Product Scraper")
st.write("Targeting: Personal Care & Fabric Care")

category_url = st.text_input("Category URL", "https://zakupy.auchan.pl/categories/higiena-i-kosmetyki/kosmetyki-do-piel%C4%99gnacji/3847")
limit = st.slider("Number of products to scrape", 1, 50, 10)

if st.button("Start Scraping"):
    async def run_scraper():
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            results = []
            st.info("Fetching product links...")
            await page.goto(category_url, wait_until="networkidle")
            
            # Extract links
            links = await page.eval_on_selector_all("a.product-card__name", "elements => elements.map(e => e.href)")
            
            progress_bar = st.progress(0)
            
            for i, link in enumerate(links[:limit]):
                await page.goto(link, wait_until="networkidle")
                
                # Logic to grab the Brand, Variant, EAN from the page
                # (Same logic as the previous script)
                item = {
                    "Brand": "Extracted Brand", # Placeholder for actual logic
                    "Variant Name": "Extracted Name",
                    "EAN": "Extracted EAN",
                    "Manufacturer": "Extracted Manu"
                }
                results.append(item)
                progress_bar.progress((i + 1) / limit)
            
            await browser.close()
            return pd.DataFrame(results)

    df = asyncio.run(run_scraper())
    st.write(df)

    # --- EXCEL EXPORT ---
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='AuchanData')
    
    st.download_button(
        label="Download Excel File",
        data=buffer.getvalue(),
        file_name="auchan_scrape_results.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
