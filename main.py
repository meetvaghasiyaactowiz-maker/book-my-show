from playwright.sync_api import sync_playwright
import time

city = 'ahmedabad'
movie = 'chand mera dil'


with sync_playwright() as p:
    browser = p.chromium.launch(
        channel="chrome",
        headless=False,
        args=[
            "--disable-blink-features=AutomationControlled",
            # "--blink-settings=imagesEnabled=false",
        ],
    )

    context = browser.new_context(
        permissions=["geolocation"],
        geolocation={"latitude": 37.7749, "longitude": -122.4194}
    )

    page = context.new_page()
    page.goto(f'https://in.bookmyshow.com/explore/home/{city}')

    page.locator("//div[contains(@class,'kudrkl')]").click()

    search = page.get_by_placeholder("Search for movies, events, plays, sports...")

    search.fill(movie)
    page.wait_for_timeout(2000)

    page.locator("//div[@id='generic']//div[contains(@class,'sc-1h5m8q1-0')]").first.click()
    page.locator("//button[@data-phase='postRelease']").first.click()
    main_show = page.locator("//div[contains(@class,'kJBeM')]").first
    main_show.locator("//div[contains(@class,'hlrCBW')]").last.click()
    page.locator("//button[@aria-label='Select Seats']").click()

    
    # Wait for canvas to be fully visible
    canvas = page.locator("canvas").first 
    canvas.wait_for(state="visible")

    # Target the layout IDs specified in your script
    target_seats = ["Seat-B-H--14", "Seat-B-H--15"]
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

            print("Looking for Accept button...")

            accept_button = page.locator("//div[class*='sc-zgl7vj-8']").filter(has_text="Accept")

            accept_button.wait_for(state="visible", timeout=5000)

            accept_button.click()
            print("Accept button clicked successfully!")

            # Wait for it to be attached/visible once colors change
            pay_button.wait_for(state="visible", timeout=5000)
            pay_button.click()
            print("Pay button clicked successfully!")
            
    else:
        print("No valid seats coordinates caught. Skipping clicks...")
        
    time.sleep(5)
    input('wait...')