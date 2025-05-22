# NikoWoL

A simple self-hosted Wake-on-LAN web client.

## Config

The application's settings are managed via a JSON configuration file.

* The primary configuration file is located at `config/config.json`.
* An example configuration with all available options is provided in `config/config.example.json`.

There are currently the following entries in the configuration file:

* **`HOST`** (string):
    * The IP address the application should bind to.
    * Set to `127.0.0.1` if you want it to be accessible only from the machine running the application.
    * Set to `0.0.0.0` to expose it to all machines on the network.
* **`PORT`** (integer, defaults to `5545`):
    * The port number the application should listen on.

## Setup - Without Docker

This section guides you through setting up and running the project directly on your machine without using Docker.

### 1. Prerequisites

Before you begin, ensure you have the following installed:

* **Git**: For cloning the repository.
* **Python 3.10+**: For running the Flask application.
* **pip**: Python package installer (comes with Python).
* **Node.js & npm**: For building Tailwind CSS. (LTS version recommended)

### 2. Clone the Repository

First, clone the project to your local machine:

```bash
git clone https://github.com/nikolan123/NikoWoL
cd NikoWoL
```

### 3. Setup Python Environment and Dependencies

Create a Python virtual environment, activate it, and install the necessary Python dependencies:

To create a virtual environment:
`python -m venv .venv`

To activate the virtual environment (choose your OS command):
* On Windows: `.venv\Scripts\activate`
* On macOS/Linux: `source .venv/bin/activate`

To install Python dependencies:
`pip install -r requirements.txt`

### 4. Install Node.js Dependencies

Install the Node.js packages required for Tailwind CSS:

`npm install`

### 5. Prepare the Configuration File

Copy the example configuration file and then modify it with your specific settings:

`cp config/config.example.json config/config.json`

Make sure to modify `config/config.json` to your needs (e.g., set your `SECRET_KEY`, any network interface settings, etc.).

### 6. Run the Application

For local development, you will typically run two processes concurrently in separate terminal windows: one for Tailwind CSS to watch for changes and one for the Flask application.

**Terminal 1: Run Tailwind CSS in Watch Mode**

This command will watch for changes in your `input.css` and HTML templates, automatically recompiling `static/css/output.css` whenever necessary.

`npm run watch:tailwind`

Or `npm run build:tailwind` if you want to build the CSS just once.

**Terminal 2: Run the Flask Application**

This command will start your Flask development server. Ensure you are in the project's root directory.

`python src/app.py`

The application should now be accessible in your browser, typically at `http://127.0.0.1:5545` (check the output in your terminal for the exact address).

## Licenses and Attributions

This project is licensed under the GNU General Public License v3.0 (GPLv3).  
See the [LICENSE](./LICENSE) file for details.

This project uses the following open-source libraries:

* **Flask** — BSD 3-Clause License  
  [https://flask.palletsprojects.com/](https://flask.palletsprojects.com/)

* **Tailwind CSS** — MIT License  
  [https://tailwindcss.com/](https://tailwindcss.com/)

* **Notyf** — MIT License  
  [https://carlosroso.com/notyf/](https://carlosroso.com/notyf/)

* **Waitress** — ZPL 2.1 License  
  [https://docs.pylonsproject.org/projects/waitress/en/latest/](https://docs.pylonsproject.org/projects/waitress/en/latest/)

* **aioping** — GNU General Public License v2 (GPL-2.0)  
  [https://github.com/stellarbit/aioping](https://github.com/stellarbit/aioping)

* **Material Icons** — Licensed under the Apache License 2.0  
  [https://github.com/google/material-design-icons](https://github.com/google/material-design-icons)
