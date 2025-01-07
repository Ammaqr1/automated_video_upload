import datetime
import time

# Define target times
target_times = [
    datetime.time(19, 22),  # 2:30 PM
    datetime.time(15, 0),   # 3:00 PM
    datetime.time(16, 15),  # 4:15 PM
    datetime.time(22, 28),  # 10:28 PM
]

def get_next_target_time(current_time, target_times):
    # Convert current_time to a datetime object for today
    current_datetime = datetime.datetime.combine(datetime.date.today(), current_time.time())

    # Find the next target time
    next_target = None
    for target in target_times:
        # Create a datetime object for the target time today
        target_datetime = datetime.datetime.combine(datetime.date.today(), target)

        # If the target time has already passed today, adjust it to tomorrow
        if target_datetime < current_datetime:
            target_datetime += datetime.timedelta(days=1)

        # If this is the first target or earlier than the current next_target, update next_target
        if next_target is None or target_datetime < next_target:
            next_target = target_datetime

    return next_target

def wait_for_next_target(current_time, next_target):
    time_diff = next_target - current_time
    if time_diff.total_seconds() > 0:
        print(f"Waiting for {time_diff.total_seconds()} seconds until {next_target.time()}")
        time.sleep(time_diff.total_seconds())
    else:
        print("Next target time is already passed. No need to wait.")

def main_single_run(target_times):
    now = datetime.datetime.now()
    print(f"Now time is {now.time()}")

    next_target = get_next_target_time(now, target_times)
    wait_for_next_target(now, next_target)

    print(f"Target time {next_target.time()} reached! Proceeding...")
    # Execute the task here
    print("Doing the task now!")

if __name__ == "__main__":
    main_single_run(target_times)