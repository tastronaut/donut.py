import math
import time
import os
import sys
from typing import List, Tuple

class ASCIIDonut:
    def __init__(self, width: int = 120, height: int = 30):
        self.width = width
        self.height = height
        self.R1 = 1.0      # Minor radius (tube thickness)
        self.R2 = 2.0      # Major radius (donut radius)
        self.K2 = 5.0      # Distance from viewer
        self.K1 = width * self.K2 * 3 / (8 * (self.R1 + self.R2))
        
        # Enhanced character sets for better shading
        self.luminance_chars = " .':!~;irsXA253hMHGS#9&@"
        self.color_chars = {
            'classic': " .':!~;irsXA253hMHGS#9&@",
            'minimal': " .-=+*#@",
            'blocks': " ░▒▓█",
            'dots': " ·∘○●"
        }
        
        # Pre-calculate common values
        self.theta_step = 0.07
        self.phi_step = 0.02
        self.chars = self.luminance_chars
        
        # Animation parameters
        self.A = 0.0  # X rotation
        self.B = 0.0  # Z rotation
        self.A_speed = 0.08
        self.B_speed = 0.03
        
        # Pre-allocate buffers for better performance
        self.output = [[' ' for _ in range(width)] for _ in range(height)]
        self.zbuffer = [[0.0 for _ in range(width)] for _ in range(height)]
        
        # Color support
        self.use_colors = self._check_color_support()
        
    def _check_color_support(self) -> bool:
        """Check if terminal supports colors"""
        return hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
    
    def _get_color_code(self, luminance: float) -> str:
        """Get ANSI color code based on luminance"""
        if not self.use_colors:
            return ""
        
        # Map luminance to color gradient (blue to yellow to red)
        if luminance < 0.2:
            return "\033[34m"  # Blue
        elif luminance < 0.4:
            return "\033[36m"  # Cyan
        elif luminance < 0.6:
            return "\033[32m"  # Green
        elif luminance < 0.8:
            return "\033[33m"  # Yellow
        else:
            return "\033[31m"  # Red
    
    def _reset_color(self) -> str:
        """Reset color to default"""
        return "\033[0m" if self.use_colors else ""
    
    def clear_screen(self):
        """Optimized screen clearing"""
        if os.name == 'nt':
            os.system('cls')
        else:
            # Use ANSI escape codes for faster clearing
            print("\033[2J\033[H", end="")
    
    def reset_buffers(self):
        """Reset output and z-buffer efficiently"""
        for y in range(self.height):
            for x in range(self.width):
                self.output[y][x] = ' '
                self.zbuffer[y][x] = 0.0
    
    def calculate_point(self, theta: float, phi: float, cosA: float, sinA: float, 
                       cosB: float, sinB: float) -> Tuple[int, int, float, float]:
        """Calculate 3D point projection and luminance"""
        # Pre-calculate trigonometric values
        costheta = math.cos(theta)
        sintheta = math.sin(theta)
        cosphi = math.cos(phi)
        sinphi = math.sin(phi)
        
        # 3D coordinates on torus surface
        circlex = self.R2 + self.R1 * costheta
        circley = self.R1 * sintheta
        
        # Apply 3D rotations
        x = circlex * (cosB * cosphi + sinA * sinB * sinphi) - circley * cosA * sinB
        y = circlex * (sinB * cosphi - sinA * cosB * sinphi) + circley * cosA * cosB
        z = self.K2 + cosA * circlex * sinphi + circley * sinA
        
        # Perspective projection
        ooz = 1 / z
        xp = int(self.width / 2 + self.K1 * ooz * x)
        yp = int(self.height / 2 - self.K1 * ooz * y)
        
        # Enhanced luminance calculation with multiple light sources
        L1 = cosphi * costheta * sinB - cosA * costheta * sinphi - sinA * sintheta + cosB * (cosA * sintheta - costheta * sinA * sinphi)
        
        # Add ambient lighting and clamp values
        luminance = max(0, L1 * 0.8 + 0.2)
        
        return xp, yp, ooz, luminance
    
    def render_frame(self):
        """Render a single frame of the donut"""
        self.reset_buffers()
        
        # Pre-calculate rotation values
        cosA = math.cos(self.A)
        sinA = math.sin(self.A)
        cosB = math.cos(self.B)
        sinB = math.sin(self.B)
        
        # Generate donut surface points
        theta = 0
        while theta < 2 * math.pi:
            phi = 0
            while phi < 2 * math.pi:
                xp, yp, ooz, luminance = self.calculate_point(
                    theta, phi, cosA, sinA, cosB, sinB
                )
                
                # Check bounds and depth
                if (0 <= xp < self.width and 0 <= yp < self.height and 
                    ooz > self.zbuffer[yp][xp]):
                    
                    self.zbuffer[yp][xp] = ooz
                    
                    # Map luminance to character
                    char_index = int(luminance * (len(self.chars) - 1))
                    char_index = max(0, min(len(self.chars) - 1, char_index))
                    
                    self.output[yp][xp] = self.chars[char_index]
                
                phi += self.phi_step
            theta += self.theta_step
    
    def display_frame(self):
        """Display the current frame with optional colors"""
        self.clear_screen()
        
        # Print header
        print(f"\033[1;37m{'='*self.width}\033[0m")
        print(f"\033[1;36m{'ASCII DONUT':^{self.width}}\033[0m")
        print(f"\033[1;37m{'='*self.width}\033[0m")
        
        # Render donut with or without colors
        for y in range(self.height):
            line = ""
            for x in range(self.width):
                char = self.output[y][x]
                if char != ' ' and self.use_colors:
                    # Add color based on character intensity
                    char_intensity = self.chars.find(char) / len(self.chars)
                    color_code = self._get_color_code(char_intensity)
                    line += f"{color_code}{char}{self._reset_color()}"
                else:
                    line += char
            print(line)
        
        # Print controls and info
        print(f"\033[1;37m{'='*self.width}\033[0m")
        color_mode = "Color" if self.use_colors else "Monochrome"
        print(f"\033[1;33mRotation: A={self.A:.2f}° B={self.B:.2f}° | Mode: {color_mode} | Press Ctrl+C to stop\033[0m")
        print(f"\033[1;32mResolution: {self.width}x{self.height} | FPS: ~30\033[0m")
    
    def set_color_mode(self, enable_colors: bool):
        """Enable or disable color output"""
        self.use_colors = enable_colors and self._check_color_support()
    
    def set_style(self, style: str):
        """Change the character style"""
        if style in self.color_chars:
            self.chars = self.color_chars[style]
        else:
            self.chars = self.luminance_chars
    
    def spin(self, duration: float = float('inf')):
        """Main animation loop"""
        start_time = time.time()
        frame_count = 0
        
        try:
            while time.time() - start_time < duration:
                frame_start = time.time()
                
                # Render and display frame
                self.render_frame()
                self.display_frame()
                
                # Update rotation angles
                self.A += self.A_speed
                self.B += self.B_speed
                
                # Maintain ~30 FPS
                frame_time = time.time() - frame_start
                target_frame_time = 1.0 / 30.0
                if frame_time < target_frame_time:
                    time.sleep(target_frame_time - frame_time)
                
                frame_count += 1
                
        except KeyboardInterrupt:
            self.clear_screen()
            elapsed = time.time() - start_time
            avg_fps = frame_count / elapsed if elapsed > 0 else 0
            print(f"\n\033[1;32mDonut stopped after {elapsed:.1f}s")
            print(f"Average FPS: {avg_fps:.1f}\033[0m")
            print(f"\033[1;36mThanks for watching the spinning donut!\033[0m\n")

def demo_styles():
    """Demonstrate different character styles"""
    print("\033[1;37mDifferent Donut Styles:\033[0m\n")
    
    styles = ['classic', 'minimal', 'blocks', 'dots']
    donut = ASCIIDonut(60, 15)
    
    for style in styles:
        donut.set_style(style)
        donut.A = 1.0
        donut.B = 1.0
        donut.render_frame()
        
        print(f"\033[1;33m{style.upper()} Style:\033[0m")
        for row in donut.output:
            print(''.join(row))
        print()

def create_donut(width: int = 120, height: int = 30, style: str = 'classic') -> ASCIIDonut:
    """Factory function to create spinning donut"""
    donut = ASCIIDonut(width, height)
    donut.set_style(style)
    return donut

def interactive_style_selector():
    """Let user choose their preferred style"""
    print("\033[1;33mChoose your donut style:\033[0m")
    print("1. Classic (detailed ASCII shading)")
    print("2. Minimal (clean and simple)")
    print("3. Blocks (solid block characters)")
    print("4. Dots (minimalist dots)")
    print("5. Show all styles demo")
    
    while True:
        try:
            choice = input("\033[1;32mEnter your choice (1-5): \033[0m").strip()
            if choice == '1':
                return 'classic'
            elif choice == '2':
                return 'minimal'
            elif choice == '3':
                return 'blocks'
            elif choice == '4':
                return 'dots'
            elif choice == '5':
                demo_styles()
                print("\033[1;33mNow choose your style for the spinning donut:\033[0m")
                continue
            else:
                print("\033[1;31mInvalid choice. Please enter 1-5.\033[0m")
        except (KeyboardInterrupt, EOFError):
            print("\n\033[1;33mUsing default classic style.\033[0m")
            return 'classic'

def interactive_color_selector():
    """Let user choose color preference"""
    print("\033[1;33mChoose your color preference:\033[0m")
    print("1. Full color (rainbow gradient)")
    print("2. Monochrome (classic black & white)")
    
    while True:
        try:
            choice = input("\033[1;32mEnter your choice (1-2): \033[0m").strip()
            if choice == '1':
                return True
            elif choice == '2':
                return False
            else:
                print("\033[1;31mInvalid choice. Please enter 1 or 2.\033[0m")
        except (KeyboardInterrupt, EOFError):
            print("\n\033[1;33mUsing default color mode.\033[0m")
            return True

def countdown(seconds: int = 3):
    """Display a countdown before starting"""
    for i in range(seconds, 0, -1):
        print(f"\033[1;36mStarting in {i}...\033[0m")
        time.sleep(1)
    print("\033[1;32mLet's spin! 🍩\033[0m")
    time.sleep(0.5)

if __name__ == "__main__":
    print("\033[1;36m" + "="*60 + "\033[0m")
    print("\033[1;37m" + "ASCII DONUT GENERATOR".center(60) + "\033[0m")
    print("\033[1;36m" + "="*60 + "\033[0m")
    print()
    
    # Let user choose style
    selected_style = interactive_style_selector()
    print()
    
    # Let user choose color preference
    use_colors = interactive_color_selector()
    
    # Show selections
    color_mode = "Full Color" if use_colors else "Monochrome"
    print(f"\033[1;33mYou selected: {selected_style.upper()} style | {color_mode} mode\033[0m")
    print()
    
    # Show countdown
    countdown(3)
    
    # Create and run the donut
    donut = create_donut(width=100, height=25, style=selected_style)
    donut.set_color_mode(use_colors)
    donut.spin()
