from playwright.sync_api import sync_playwright
from datetime import datetime
import time

book_url = "https://in.bookmyshow.com/explore/home/ahmedabad"

if not book_url:
    print("URL Not Entered!")
    exit()

print(f"\nTARGET URL: {book_url}")

start_time = datetime.now()
with sync_playwright() as p:

    browser = p.chromium.launch(
        channel="chrome",
        headless=False,  
        args=["--disable-blink-features=AutomationControlled"],
    )

    context = browser.new_context(viewport={"width": 1280, "height": 800})
    page = context.new_page()
    
    print("Navigating to BookMyShow...")
    page.goto(book_url)
    
    print("Selecting movie...")
    page.locator("a[href*='chand-mera-dil']").first.click()
    
    print("Clicking 'Book tickets'...")
    page.get_by_role("button", name="Book tickets").click()
    
    print("Selecting showtime (10:10 PM)...")
    page.locator("div").filter(has_text="10:10 PM").last.click()
    
    # Wait for seat selector acceptance modal if any
    page.locator("//button[@aria-label='Select Seats']").click()
    
    print("Interacting with the seat layout Canvas via Konva Context...")

    # Wait for canvas to be fully visible
    canvas = page.locator("canvas").first 
    canvas.wait_for(state="visible")

    # Target the layout IDs specified in your script
    target_seats = ["Seat-B-K--01", "Seat-B-K--02"]
    seat_coords = []

    for seat_id in target_seats:
        # Use Konva's client rect mapping to transform internal coordinates accurately to viewport space
        coordinates = page.evaluate("""
            (targetId) => {
                if (typeof Konva !== 'undefined' && Konva.stages && Konva.stages.length > 0) {
                    const stage = Konva.stages[0];
                    
                    const seatNode = stage.findOne((node) => {
                        return node.attrs && (node.attrs.id === targetId || node.attrs.seatId === targetId || node.attrs.name === targetId);
                    });
                    
                    if (seatNode) {
                        // getClientRect takes stage scale and absolute positioning into account relative to the canvas element
                        const rect = seatNode.getClientRect();
                        
                        return {
                            x: rect.x + (rect.width / 2),
                            y: rect.y + (rect.height / 2),
                            found: true
                        };
                    }
                }
                return { found: false };
            }
        """, seat_id)
        
        if coordinates["found"]:
            print(f"Found {seat_id} at canvas relative X: {coordinates['x']}, Y: {coordinates['y']}")
            seat_coords.append(coordinates)
        else:
            print(f"Could not find coordinates for {seat_id} via Konva API.")

    # Click the seats using Playwright mouse controls
    if len(seat_coords) > 0:
        box = canvas.bounding_box()
        if box:
            for coord in seat_coords:
                # Add the relative canvas coordinates to the canvas absolute position on the screen
                click_x = box["x"] + coord["x"]
                click_y = box["y"] + coord["y"]
                
                # Move to position first to trigger hover states if necessary, then click
                page.mouse.move(click_x, click_y)
                page.mouse.click(click_x, click_y)
                print(f"Clicked on coordinates: X={click_x}, Y={click_y}")
                time.sleep(0.6) # Small buffer to let state update
                
            # --- Click the checkout/pay amount button ---
            print("Looking for payment button...")
            
            # Safe selector using partial base class identification
            pay_button = page.locator("div[class*='sc-zgl7vj-8']")

            pay_button.wait_for(state="visible", timeout=5000)
            pay_button.click()
            print("Pay button clicked successfully!")
            
            page.locator("//button[@aria-label='Accept']").click()

            page.locator("//div[contains(@class,'kZRwsA')]").click()
            input('wait..')
            
    else:
        print("No valid seats coordinates caught. Skipping clicks...")
        
    time.sleep(5) # Keep open momentarily to view selection
    browser.close()

    # sc-zgl7vj-8 fUiPnc