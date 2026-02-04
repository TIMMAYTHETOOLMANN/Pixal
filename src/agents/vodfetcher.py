"""VODFetcher agent for downloading VODs from streaming platforms."""
import os


class VODFetcher:
    """Downloads VODs from Twitch, YouTube, and other supported platforms using yt-dlp."""

    def __init__(self):
        print("[📥 INIT] VODFetcher ready")

    def download(self, url: str, output_path: str = "stream_input.mp4") -> bool:
        """Download a VOD from the given URL.
        
        Args:
            url: The VOD URL (Twitch, YouTube, etc.)
            output_path: Where to save the downloaded video
            
        Returns:
            bool: True if download succeeded, False otherwise
            
        Note:
            Prefers mp4 format when available. If mp4 is not available, 
            yt-dlp will download the best available format and may 
            convert/remux it to the output path specified.
        """
        try:
            import yt_dlp
        except ImportError:
            print("[❌] yt-dlp not installed. Run: pip install yt-dlp")
            return False

        print(f"[📥] Downloading VOD from {url}")
        
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': output_path,
            'quiet': False,
            'no_warnings': False,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            if os.path.exists(output_path):
                print(f"[✅] VOD downloaded to {output_path}")
                return True
            else:
                print(f"[❌] Download completed but file not found at {output_path}")
                return False
                
        except Exception as e:
            print(f"[❌] VOD download failed: {e}")
            return False
