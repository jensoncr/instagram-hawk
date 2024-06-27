<<<<<<< HEAD
# Instagram Hawk

Instagram Hawk is a script designed to monitor specified Instagram accounts for new posts, download the media, process the content by removing metadata and adjusting contrast, generate captions using a language model, and re-upload the processed content to your own Instagram account.

## Features

- Monitor specified Instagram accounts for new posts.
- Download and process photos and videos to remove metadata and adjust contrast.
- Generate captions using a pretrained language model.
- Re-upload the processed content to your Instagram account.

## Installation

1. **Clone the repository:**

    ```sh
    git clone https://github.com/jensoncr/instagram-hawk.git
    cd instagram-hawk
    ```

2. **Set up a virtual environment:**

    ```sh
    conda create --name myenv python=3.9
    conda activate myenv
    ```

3. **Install the required packages:**

    ```sh
    pip install -r requirements.txt
    ```

4. **Install additional dependencies:**
    - Follow the instructions to install [ffmpeg](https://ffmpeg.org/download.html).

5. **Set up credentials:**

    - Create a `credentials.txt` file in the root directory with your Instagram username and password on separate lines.
    - Example `credentials.txt`:
      ```
      your_username
      your_password
      ```

6. **Create the necessary directories:**

    ```sh
    mkdir tmpdown
    mkdir processed_content
    ```

## Usage

1. **Run the script:**

    ```sh
    python main.py
    ```

    - The script will read your Instagram credentials from `credentials.txt`, log in, and start monitoring the specified accounts for new posts.

2. **Customizing the monitored accounts:**

    - Edit the `usernames_to_monitor` list in `main.py` to include the usernames of the accounts you want to monitor.

    ```python
    usernames_to_monitor = ["repostlocker"]
    ```

## Security

To keep your credentials secure:

- Add `credentials.txt` and `session.json` to your `.gitignore` file to prevent them from being pushed to the repository.

    ```sh
    echo "credentials.txt" >> .gitignore
    echo "session.json" >> .gitignore
    ```

## Contributing

If you would like to contribute to this project, please fork the repository and submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
=======
# instagram-hawk
using instagrapi, monitors accounts and reposts media 
>>>>>>> c544a288f44af6261f3a4a12801ffe762130316b
