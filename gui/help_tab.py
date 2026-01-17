from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QScrollArea,
    QLabel,
    QFrame,
    QSizePolicy,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class HelpTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        
        # Create scroll area for help content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Container widget for help content
        container = QWidget()
        container.setAttribute(Qt.WA_StyledBackground, True)
        container.setStyleSheet('background: white; padding: 8px;')
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel('EVE Config Copier (ECC) - User Guide')
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet('color: #2196F3; margin-bottom: 10px;')
        title.setAlignment(Qt.AlignHCenter)
        container_layout.addWidget(title)
        
        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet('color: #ddd; margin: 10px 0;')
        container_layout.addWidget(separator)
        
        # AI Warning Banner
        warning_banner = QLabel('⚠️ Warning: Written by AI. Use your own brain when in doubt.')
        warning_banner.setWordWrap(True)
        warning_banner.setAlignment(Qt.AlignHCenter)
        warning_banner.setStyleSheet('''
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 6px;
            padding: 8px 12px;
            margin: 10px 0;
            color: #856404;
            font-weight: bold;
            font-size: 12px;
        ''')
        container_layout.addWidget(warning_banner)
        
        # Overview section
        self._add_section(container_layout, "Overview", """
This application helps you manage EVE Online character settings and configurations. It can scan your EVE installation directory to find character data, cache character information, and copy settings between characters and profiles.
        """)
        
        # Getting Started section
        self._add_section(container_layout, "Getting Started", """
<b>1. First Time Setup:</b>
• Click the <b>Configure</b> button in the All Characters tab
• Select your EVE Online installation directory
• The application will automatically detect your game files

<b>2. Scan for Characters:</b>
• Click the <b>Scan</b> button to discover all characters and accounts
• This creates a mappings.json file with character and account relationships
• You only need to scan once, or when you add new characters

<b>3. Prefetch Character Data:</b>
• Click <b>Prefetch cache</b> to download character names and portraits
• This improves the display and makes character selection easier
• Run this periodically to keep character information up to date
        """)
        
        # All Characters Tab section
        self._add_section(container_layout, "All Characters Tab", """
The All Characters tab displays all discovered characters organized by account.

<b>Button Functions:</b>
• <b>Configure:</b> Opens the configuration dialog to set up EVE directory paths
• <b>Scan:</b> Scans your EVE installation for characters and accounts
• <b>Prefetch cache:</b> Downloads character names and portraits from EVE servers
• <b>Delete All:</b> Removes all account data from mappings (does not delete game files)

<b>Account Management:</b>
• Each account is displayed as a gray header bar
• Characters belonging to that account are shown below with portraits
• Click the red "Delete" button on an account to remove it from the list
• Character portraits show corporation logos in the bottom-right corner

<b>Character Display:</b>
• Character portraits are 80x80 pixels with names underneath
• Names are automatically shortened if too long to fit
• Missing portraits show as gray placeholders until prefetch is run
        """)
        
        # Copy Config Tab section
        self._add_section(container_layout, "Copy Config Tab", """
The Copy Config tab allows you to copy character settings between characters and profiles.

<b>Source Selection:</b>
1. <b>Server:</b> Choose Main server (Tranquility) or Test server (Singularity)
2. <b>Profile:</b> Select which EVE profile contains the source settings
3. <b>Character Search:</b> Type to search and select the source character
4. <b>Account Info:</b> Shows which account the character belongs to
5. <b>Status Indicators:</b> Green/red dots show if account and character files exist

<b>Destination Selection:</b>
1. <b>Server:</b> Choose destination server (can be same or different)
2. <b>Profile:</b> Select existing profile OR check "new profile" to create one
3. <b>New Profile:</b> Enter name for new profile (warning shows if name exists)
4. <b>Character Tree:</b> Select which characters to copy settings to
   • Use "Expand All" / "Collapse All" to manage tree view
   • Use "Select All" checkbox to select/deselect all characters
   • Individual characters can be selected by checking their boxes

<b>Copy Preview:</b>
• Shows source character and destination details
• Lists all files that will be copied or created
• Preview updates automatically as you make selections

<b>Settings Copy Process:</b>
• Character-specific settings (core_char_*.dat) are always copied
• Account settings (core_user_*.dat) are copied based on these rules:
  - If "Use account config as well" is checked: always copy/overwrite
  - If unchecked: only copy if destination account file doesn't exist
• When creating new profiles, template files are copied first
        """)
        
        # File Structure section
        self._add_section(container_layout, "File Structure", """
<b>EVE Directory Structure:</b>
• <b>Main Server:</b> c_ccp_eve_tq_tranquility/
• <b>Test Server:</b> c_ccp_eve_sisi_singularity/
• <b>Profiles:</b> settings_[ProfileName]/ (e.g., settings_default/)

<b>Important Files:</b>
• <b>core_char_[ID].dat:</b> Character-specific settings
• <b>core_user_[ID].dat:</b> Account-specific settings
• <b>core_char__.dat:</b> Default character template
• <b>core_user__.dat:</b> Default account template
• <b>core_public__.yaml:</b> Public settings
• <b>prefs.ini:</b> Client preferences

<b>Cache Files:</b>
• <b>cache/char/[ID].json:</b> Character information (name, corporation)
• <b>cache/corp/[ID].json:</b> Corporation information
• <b>cache/img/char/[ID]:</b> Character portraits
• <b>cache/img/corp/[ID]:</b> Corporation logos
        """)
        
        # Common Workflows section
        self._add_section(container_layout, "Common Workflows", """
<b>Setting up a new character with existing settings:</b>
1. Go to All Characters tab and run Scan if needed
2. Switch to Copy Config tab
3. Select source server and profile
4. Search for and select the character with desired settings
5. Select destination server and profile
6. Check the new character in the character tree
7. Click "Copy Settings"

<b>Creating a new profile with settings:</b>
1. In Copy Config tab, select source character as above
2. For destination, select target server
3. Check "new profile" and enter a unique name
4. Select characters to copy to
5. Click "Copy Settings" - this creates the profile with templates first

<b>Copying account settings:</b>
1. Follow normal copy process
2. Check "Use account config as well" to overwrite existing account files
3. Leave unchecked to preserve existing account settings

<b>Managing multiple accounts:</b>
1. Use the All Characters tab to see which characters belong to which accounts
2. Delete unwanted accounts using the red Delete button
3. Re-scan if you add new accounts to EVE
        """)
        
        # Troubleshooting section
        self._add_section(container_layout, "Troubleshooting", """
<b>Configuration Issues:</b>
• If Configure can't find EVE: manually browse to your EVE installation
• If Scan finds no characters: ensure EVE has been launched at least once
• If profiles don't appear: check that the selected server directory exists

<b>Character Issues:</b>
• If characters show as numbers: run Prefetch cache to get names
• If portraits don't appear: check internet connection and run Prefetch cache
• If character not in list: run Scan again to refresh character data

<b>Copy Issues:</b>
• "Source character file not found": the character hasn't logged in on that profile
• "Profile name already exists": choose a different name or use existing profile
• "No destinations selected": check at least one character in the tree

<b>File Access Issues:</b>
• Ensure EVE is closed when copying settings
• Check that you have write permissions to the EVE directory
• On Windows, run as administrator if needed
        """)
        
        # Footer
        footer = QLabel('For more help, check the README.md file or create an issue on the project repository.')
        footer.setStyleSheet('color: #666; font-style: italic; margin-top: 20px; text-align: center;')
        footer.setAlignment(Qt.AlignHCenter)
        footer.setWordWrap(True)
        container_layout.addWidget(footer)
        
        # Add stretch to push content to top
        container_layout.addStretch()
        
        # Set container as scroll widget
        scroll.setWidget(container)
        self.layout.addWidget(scroll)
        
        # Allow tab to expand
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    
    def _add_section(self, layout, title: str, content: str):
        """Add a section with title and content to the layout."""
        # Section title
        section_title = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        section_title.setFont(title_font)
        section_title.setStyleSheet('color: #333; margin-top: 20px; margin-bottom: 10px;')
        layout.addWidget(section_title)
        
        # Section content - process text for proper HTML display
        html_content = self._format_text_for_html(content.strip())
        section_content = QLabel(html_content)
        section_content.setWordWrap(True)
        section_content.setStyleSheet('''
            color: #555;
            line-height: 1.6;
            margin-bottom: 15px;
            padding: 10px;
            background: #f9f9f9;
            border-left: 4px solid #2196F3;
            border-radius: 4px;
        ''')
        # Enable rich text for bold formatting
        section_content.setTextFormat(Qt.RichText)
        layout.addWidget(section_content)
    
    def _format_text_for_html(self, text: str) -> str:
        """Convert plain text with markdown-like formatting to proper HTML."""
        lines = text.split('\n')
        html_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:  # Empty line
                html_lines.append('<br>')
            elif line.startswith('•'):  # Bullet point
                html_lines.append('&nbsp;&nbsp;&nbsp;• ' + line[1:].strip() + '<br>')
            else:  # Regular line
                html_lines.append(line + '<br>')
        
        return ''.join(html_lines)