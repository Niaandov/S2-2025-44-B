import random as rand
import time
import keyboard #this is just to stop the simulation otherwise it will run endlessly

def simulate_packaging(pace):
    pace_speeds = {
        "Slow": 1.5,
        "Medium": 1.0,
        "Fast": 0.5
    }

    box_sizes = {
        "low": 4,
        "medium": 5,
        "fast": 6
    }

    #setting error rate based on the speed (figured faster the program runs the more likely to error)
    if pace.lower() == "slow":
        min_error, max_error = 5, 9
    elif pace.lower() == "medium":
        min_error, max_error = 9, 12
    else:
        min_error, max_error = 12, 15

    #declaring variables:
    # delay = pace_speeds.get(pace, 1.0)
    delay = pace_speeds.get(pace)
    total_items = 0
    total_boxes = 0
    errors = 0
    run = 0

    print(f"\n--- Packaging Task Simulation ---")
    print(f"Pace: {pace}")
    print(f"Error Rate: {min_error}-{max_error}% per item")
    print(f"Press ESC to stop simulation.\n")

    while True:
        if keyboard.is_pressed('esc'): #hold down esc at the end of a cycle/run to stop the program
            print("\n--- Simulation Stopped ---")
            break

        run += 1
        #randomly pick a box size each run:
        box_level = rand.choice(list(box_sizes.keys()))
        box_size = box_sizes[box_level]

        #randomise the error rate for the selected box size:
        error_rate = rand.randint(min_error, max_error)

        print(f"\n--- Packagaing Box {run} ({box_level.title()} size: {box_size} items, Error Rate: {error_rate}%) ---")
        box_items = 0
        box_errors = 0

        while box_items < box_size:
            total_items += 1
            box_items += 1

            if rand.randint(1, 100) <= box_size:
                print(f"Error: Item {box_items} in box {run} failed packaging.")
                errors += 1
                box_errors += 1
            else:
                print(f"Item {box_items} in box {run} packaged successfully.")
            
            time.sleep(delay)

        total_boxes += 1
        print(f" Box {run} sealed with {box_items} items, {box_errors} errors.\n")

        print(f"Total Boxes Packed: {total_boxes}")
        print(f"Total Items Processed: {total_items}")
        print(f"Successful Items: {total_items - errors}")
        print(f"Errors: {errors} ({(errors/total_items)*100:.2f}%)")
    
    print("\n--- Simulation Complete ---")
    print(f"Total Boxes Packed: {total_boxes}")
    print(f"Total Items Processed: {total_items}")
    print(f"Successful Items: {total_items - errors}")
    print(f"Errors: {errors} ({(errors/total_items)*100:.2f}%)")


simulate_packaging("Fast")

