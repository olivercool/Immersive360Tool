import os
import subprocess

def convert_dual_insv_to_equirectangular(input_front, input_back, output_path, ffmpeg_path=r".\ffmpeg.exe"):
    """
    Rotates raw Insta360 ONE X2 lens feeds, applies 200° FOV mapping, and forces
    a 2:1 standard equirectangular output resolution (5760x2880).
    """
    # Updated filter graph with 200° FOV and explicit 2:1 resolution (5760x2880)
    filter_graph = (
        "[0:v]transpose=clock[front];"
        "[1:v]transpose=cclock[back];"
        "[front][back]hstack[dual];"
        "[dual]v360=input=dfisheye:output=equirect:ih_fov=200:iv_fov=200:w=5760:h=2880"
    )

    ffmpeg_cmd = [
        ffmpeg_path,
        "-y",
        "-i", input_front,
        "-i", input_back,
        "-filter_complex", filter_graph,
        "-c:v", "h264_nvenc",
        "-cq", "18",
        "-preset", "p4",
        "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        output_path
    ]

    print("Executing local FFmpeg conversion...\n")

    try:
        subprocess.run(ffmpeg_cmd, check=True)
        print(f"Successfully generated 2:1 equirectangular video: {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error running FFmpeg command: {e}")
    except FileNotFoundError:
        print(f"Could not find local FFmpeg at '{ffmpeg_path}'. Check path and try again.")

if __name__ == "__main__":
    INPUT_FRONT_INSV = "VID_00_001.insv"
    INPUT_BACK_INSV = "VID_10_001.insv"
    OUTPUT_360_VIDEO = "output_equirectangular.mp4"

    if os.path.exists(INPUT_FRONT_INSV) and os.path.exists(INPUT_BACK_INSV):
        convert_dual_insv_to_equirectangular(INPUT_FRONT_INSV, INPUT_BACK_INSV, OUTPUT_360_VIDEO)
    else:
        print(f"Error: Ensure '{INPUT_FRONT_INSV}' and '{INPUT_BACK_INSV}' are in this directory.")
