import subprocess


def run_seeder(module_name: str):
    print(f"\n🔄 Running seeder: {module_name}")
    try:
        result = subprocess.run(
            ["python", "-m", module_name],
            check=True,
            capture_output=True,
            text=True,
        )
        print(result.stdout)
        print(f"Seeder finished: {module_name}")
    except subprocess.CalledProcessError as e:
        print(f"Seeder failed: {module_name}")
        print(f"Return code: {e.returncode}")
        print(f"Error output:\n{e.stderr}")
        raise


def main():
    seeders_in_order = [
        "app.seeders.1_users",
        "app.seeders.2_categories",
        "app.seeders.3_addresses",
        "app.seeders.4_user_reviews",
        "app.seeders.5_users_listings",
        "app.seeders.6_liked_listings",
        "app.seeders.7_listing_categories",
    ]

    for seeder in seeders_in_order:
        try:
            run_seeder(seeder)
        except subprocess.CalledProcessError:
            break  # stop on first failure (or use `continue` to skip)


if __name__ == "__main__":
    main()
