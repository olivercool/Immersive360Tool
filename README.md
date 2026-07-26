# Immersive360Tool

Converts a single 360 recording into a full resolution top/bottom 3D video using DA2. Additionally, it can convert dual `.insv` files into an equirectangular video.

## Installation of the "360 to 3D" program

Actually, you don't even have to install if you don't want to! These programs can work in Google Colab or Kaggle, which are both free.

<details>
<summary><b>Okay, I want to run it in the cloud</b></summary>
<br>

Great, but it's very important to know which service you'll use:
* **Google Colab:** Use if you want simplicity and ease of setup, but Colab requires you to have the website open for the entirety of the processing.
* **Kaggle:** Use if you want to start the process, shut down your computer, then come back to the output later. Kaggle is a bit confusing to set up, though.

<details>
<summary>I want to use Google Colab</summary>
<br>

1. Go to [this Colab Notebook](https://colab.research.google.com/drive/1JIb2ms_VgNmsLnpLojyOWj1e9Vfm7Mgk?usp=sharing) and click **Run all**.
2. Rename your input file to `input_360.mp4`.
3. The script will prompt you for your 360 video, and will output the top/bottom 3D equirectangular video when finished.

</details>

<details>
<summary>I want to use Kaggle</summary>
<br>

I personally use this method the most, but I'm too lazy today to write a guide on how to set it up. Sorry, gl bro.

</details>
</details>

<details>
<summary><b>I want to run this on my PC, LOCALLY</b></summary>
<br>

**Warning:** Make sure your PC's CPU is beefy enough, and you're willing to keep it running for the entirety of the processing!

1. Simply download `PC_process_360_rgbd.py`, and rename your input file to `input.mp4`.
2. Download and install some form of `ffmpeg-essentials` accessible inside the folder where `PC_process_360_rgbd.py` is located.
3. Finally, run the file!

</details>

---

## Installation of the ".insv to 360" program

Actually, you don't even have to install if you don't want to! These programs can work in Google Colab or Kaggle, which are both free.

<details>
<summary><b>Okay, I want to run it in the cloud</b></summary>
<br>

Great, but it's very important to know which service you'll use:
* **Google Colab:** Use if you want simplicity and ease of setup, but Colab requires you to have the website open for the entirety of the processing.
* **Kaggle:** Use if you want to start the process, shut down your computer, then come back to the output later. Kaggle is a bit confusing to set up, though.

<details>
<summary>I want to use Google Colab</summary>
<br>

1. Go to [STILL WORKING ON THIS] and click **Run all**.
2. Rename your input file to `input.mp4`.
3. The script will prompt you for your `.insv` files (**BE SURE TO SELECT BOTH OF THEM**), and will output the 360 equirectangular video when finished.

</details>

<details>
<summary>I want to use Kaggle</summary>
<br>

I personally use this method the most, but I'm too lazy today to write a guide on how to set it up. Sorry, gl bro.

</details>
</details>

<details>
<summary><b>I want to run this on my PC, LOCALLY</b></summary>
<br>

**Warning:** Make sure your PC's CPU is beefy enough, and you're willing to keep it running for the entirety of the processing!

1. Simply download `PC_insvto360.py`, and rename your input file to `input.mp4`.
2. Download and install some form of `ffmpeg-essentials` accessible inside the folder where `PC_insvto360.py` is located.
3. Finally, run the file!

</details>
