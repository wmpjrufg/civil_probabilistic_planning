import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("Acessando o app...")
        await page.goto("https://civilprobabilisticplanning.streamlit.app/")
        
        # Espera um pouco para o JavaScript carregar a tela de sono
        await page.wait_for_timeout(5000)
        
        # Procura pelo botão azul de "Wake up"
        button_selector = 'button:has-text("Yes, get this app back up!")'
        wake_up_button = await page.query_selector(button_selector)
        
        if wake_up_button:
            print("App dormindo! Clicando no botão para acordar...")
            await wake_up_button.click()
            # Espera o app carregar após o clique
            await page.wait_for_timeout(10000)
            print("Comando de despertar enviado com sucesso.")
        else:
            print("O app já está acordado ou a estrutura da página mudou.")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())