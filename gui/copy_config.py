from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QCheckBox,
    QSizePolicy,
    QAbstractItemView,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QCompleter,
    QTreeWidget,
    QTreeWidgetItem,
    QScrollArea,
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, Signal, QStringListModel
from pathlib import Path
import json
import shutil
from eve_backend.cache import CacheManager


class CopyConfigTab(QWidget):
    """New look: a single styled line with a character dropdown (by name),
    account label after it, and a checkbox 'Use account config all'.

    All prior elements were removed as requested.
    """

    def __init__(self, mappings_path: str = None, parent=None):
        super().__init__(parent)
        self.cache = CacheManager()
        self.mappings_path = Path(mappings_path) if mappings_path else Path.cwd() / 'mappings.json'
        self.layout = QVBoxLayout(self)

        # thin title bar above the row, similar to AllCharacters account line
        header = QWidget()
        header.setAttribute(Qt.WA_StyledBackground, True)
        header.setStyleSheet('background:#eee; padding:2px;')
        header_l = QHBoxLayout(header)
        header_l.setContentsMargins(8, 2, 8, 2)
        header_label = QLabel('Select settings to copy from character to other characters')
        header_label.setStyleSheet('font-weight: bold; color:#222;')
        header_l.addWidget(header_label)
        # Add stretch to push label to the left
        header_l.addStretch()
        # keep header compact — do not stretch elements
        header.setFixedHeight(24)
        self.layout.addWidget(header)

        # server and profile selection row
        profile_row = QWidget()
        profile_row.setAttribute(Qt.WA_StyledBackground, False)
        profile_row.setStyleSheet('padding:4px;')
        profile_row_l = QHBoxLayout(profile_row)
        profile_row_l.setContentsMargins(8, 4, 8, 4)
        
        # server selection dropdown
        server_label = QLabel('Server:')
        server_label.setStyleSheet('font-weight: bold; color:#222; padding-right:4px;')
        profile_row_l.addWidget(server_label)
        
        self.server_combo = QComboBox()
        self.server_combo.addItem('-- Select Server --', None)  # Blank default option
        self.server_combo.addItem('Main server', 'c_ccp_eve_tq_tranquility')
        self.server_combo.addItem('Test server', 'c_ccp_eve_sisi_singularity')
        self.server_combo.setMaximumWidth(150)
        self.server_combo.currentIndexChanged.connect(self._on_server_changed)
        profile_row_l.addWidget(self.server_combo)
        
        # profile selection dropdown
        profile_label = QLabel('Profile:')
        profile_label.setStyleSheet('font-weight: bold; color:#222; padding-left:12px; padding-right:4px;')
        profile_row_l.addWidget(profile_label)
        
        self.profile_combo = QComboBox()
        self.profile_combo.setMaximumWidth(200)
        self.profile_combo.currentIndexChanged.connect(self._on_profile_changed)
        profile_row_l.addWidget(self.profile_combo)
        
        # Add stretch to push elements to the left
        profile_row_l.addStretch()
        
        profile_row.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        profile_row.setFixedHeight(32)  # Fixed height to prevent vertical stretching
        self.layout.addWidget(profile_row, 0, Qt.AlignLeft | Qt.AlignTop)

        # styled inputs row (plain background) placed directly under header
        row = QWidget()
        row.setAttribute(Qt.WA_StyledBackground, False)
        row.setStyleSheet('padding:4px;')
        row_l = QHBoxLayout(row)
        row_l.setContentsMargins(8, 4, 8, 4)

        # searchable field: QLineEdit with QCompleter for filtering
        self.char_search = QLineEdit()
        self.char_search.setPlaceholderText('Type to search characters...')
        self.char_search.setMaximumWidth(360)
        self.char_search.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        row_l.addWidget(self.char_search)

        # use QCompleter for autocomplete - handles focus properly
        self._completer = QCompleter()
        self._completer.setCaseSensitivity(Qt.CaseInsensitive)
        self._completer.setFilterMode(Qt.MatchContains)
        self._completer.setCompletionMode(QCompleter.PopupCompletion)
        self._model = QStringListModel()
        self._completer.setModel(self._model)
        self.char_search.setCompleter(self._completer)
        
        # connect when user selects from completer
        self._completer.activated.connect(self._on_completer_activated)
        
        # connect when input loses focus to trigger updates
        self.char_search.editingFinished.connect(self._on_char_input_finished)

        self.account_label = QLabel('')
        self.account_label.setStyleSheet('font-weight: bold; color:#222; padding-left:8px;')
        self.account_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        row_l.addWidget(self.account_label)

        self.use_account_cfg_chk = QCheckBox('Use account config as well')
        self.use_account_cfg_chk.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.use_account_cfg_chk.toggled.connect(self._on_account_config_toggled)
        row_l.addWidget(self.use_account_cfg_chk)
        
        # Add stretch to push elements to the left
        row_l.addStretch()
        
        # keep elements stacked to the left, no stretching
        row.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        row.setFixedHeight(32)  # Fixed height to prevent vertical stretching
        self.layout.addWidget(row, 0, Qt.AlignLeft | Qt.AlignTop)

        # status check row for data files
        status_row = QWidget()
        status_row.setAttribute(Qt.WA_StyledBackground, False)
        status_row.setStyleSheet('padding:4px;')
        status_row_l = QHBoxLayout(status_row)
        status_row_l.setContentsMargins(8, 4, 8, 4)

        # Status labels with colored indicators
        self.account_status_label = QLabel('Account')
        self.account_status_label.setStyleSheet('font-weight: bold; color:#222; padding-right:4px;')
        status_row_l.addWidget(self.account_status_label)

        self.account_indicator = QLabel('●')
        self.account_indicator.setStyleSheet('color:#ccc; font-size:12px; padding-right:8px;')  # Default gray
        status_row_l.addWidget(self.account_indicator)

        self.char_status_label = QLabel('Character')
        self.char_status_label.setStyleSheet('font-weight: bold; color:#222; padding-left:8px; padding-right:4px;')
        status_row_l.addWidget(self.char_status_label)

        self.char_indicator = QLabel('●')
        self.char_indicator.setStyleSheet('color:#ccc; font-size:12px; padding-right:8px;')  # Default gray
        status_row_l.addWidget(self.char_indicator)

        # Add stretch to push elements to the left
        status_row_l.addStretch()

        status_row.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        status_row.setFixedHeight(32)  # Fixed height to prevent vertical stretching
        self.layout.addWidget(status_row, 0, Qt.AlignLeft | Qt.AlignTop)

        # copy settings header
        copy_header = QWidget()
        copy_header.setAttribute(Qt.WA_StyledBackground, True)
        copy_header.setStyleSheet('background:#eee; padding:2px;')
        copy_header_l = QHBoxLayout(copy_header)
        copy_header_l.setContentsMargins(8, 2, 8, 2)
        copy_header_label = QLabel('Copy setting to')
        copy_header_label.setStyleSheet('font-weight: bold; color:#222;')
        copy_header_l.addWidget(copy_header_label)
        # Add stretch to push label to the left
        copy_header_l.addStretch()
        # keep header compact — do not stretch elements
        copy_header.setFixedHeight(24)
        self.layout.addWidget(copy_header)

        # destination server and profile selection row
        dest_profile_row = QWidget()
        dest_profile_row.setAttribute(Qt.WA_StyledBackground, False)
        dest_profile_row.setStyleSheet('padding:4px;')
        dest_profile_row_l = QHBoxLayout(dest_profile_row)
        dest_profile_row_l.setContentsMargins(8, 4, 8, 4)
        
        # destination server selection dropdown
        dest_server_label = QLabel('Server:')
        dest_server_label.setStyleSheet('font-weight: bold; color:#222; padding-right:4px;')
        dest_profile_row_l.addWidget(dest_server_label)
        
        self.dest_server_combo = QComboBox()
        self.dest_server_combo.addItem('-- Select Server --', None)  # Blank default option
        self.dest_server_combo.addItem('Main server', 'c_ccp_eve_tq_tranquility')
        self.dest_server_combo.addItem('Test server', 'c_ccp_eve_sisi_singularity')
        self.dest_server_combo.setMaximumWidth(150)
        self.dest_server_combo.currentIndexChanged.connect(self._on_dest_server_changed)
        dest_profile_row_l.addWidget(self.dest_server_combo)
        
        # destination profile selection dropdown
        dest_profile_label = QLabel('Profile:')
        dest_profile_label.setStyleSheet('font-weight: bold; color:#222; padding-left:12px; padding-right:4px;')
        dest_profile_row_l.addWidget(dest_profile_label)
        
        self.dest_profile_combo = QComboBox()
        self.dest_profile_combo.setMaximumWidth(200)
        self.dest_profile_combo.currentIndexChanged.connect(self._on_dest_profile_changed)
        dest_profile_row_l.addWidget(self.dest_profile_combo)
        
        # new profile checkbox
        self.new_profile_chk = QCheckBox('new profile')
        self.new_profile_chk.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.new_profile_chk.setStyleSheet('padding-left:12px;')
        self.new_profile_chk.toggled.connect(self._on_new_profile_toggled)
        dest_profile_row_l.addWidget(self.new_profile_chk)
        
        # new profile name input field
        self.new_profile_input = QLineEdit()
        self.new_profile_input.setPlaceholderText('Enter new profile name...')
        self.new_profile_input.setMaximumWidth(200)
        self.new_profile_input.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.new_profile_input.setEnabled(False)  # Initially disabled
        self.new_profile_input.textChanged.connect(self._on_new_profile_text_changed)
        dest_profile_row_l.addWidget(self.new_profile_input)
        
        # profile exists warning label
        self.profile_warning = QLabel('⚠ Profile exists')
        self.profile_warning.setStyleSheet('color:#f44336; font-weight:bold; padding-left:8px;')
        self.profile_warning.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.profile_warning.setVisible(False)  # Initially hidden
        dest_profile_row_l.addWidget(self.profile_warning)
        
        # Add stretch to push elements to the left
        dest_profile_row_l.addStretch()
        
        dest_profile_row.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        dest_profile_row.setFixedHeight(32)  # Fixed height to prevent vertical stretching
        self.layout.addWidget(dest_profile_row, 0, Qt.AlignLeft | Qt.AlignTop)

        # character and account selection tree view section
        tree_section = QWidget()
        tree_section.setAttribute(Qt.WA_StyledBackground, False)
        tree_section_l = QHBoxLayout(tree_section)
        tree_section_l.setContentsMargins(0, 8, 0, 0)
        
        # Left side: tree view and controls
        tree_container = QWidget()
        tree_container.setAttribute(Qt.WA_StyledBackground, False)
        tree_container_l = QVBoxLayout(tree_container)
        tree_container_l.setContentsMargins(8, 0, 8, 0)
        
        # Tree controls section
        # Label on its own line
        tree_label_container = QWidget()
        tree_label_container.setAttribute(Qt.WA_StyledBackground, False)
        tree_label_l = QHBoxLayout(tree_label_container)
        tree_label_l.setContentsMargins(0, 0, 0, 2)
        
        tree_label = QLabel('Select characters/accounts to copy to:')
        tree_label.setStyleSheet('font-weight: bold; color:#222;')
        tree_label_l.addWidget(tree_label)
        tree_label_l.addStretch()
        
        tree_label_container.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        tree_container_l.addWidget(tree_label_container)
        
        # Controls on their own line
        tree_controls = QWidget()
        tree_controls.setAttribute(Qt.WA_StyledBackground, False)
        tree_controls_l = QHBoxLayout(tree_controls)
        tree_controls_l.setContentsMargins(0, 0, 0, 4)
        
        # Single expand/collapse toggle button
        self.expand_collapse_btn = QPushButton('Expand All')
        self.expand_collapse_btn.setMaximumWidth(100)
        self.expand_collapse_btn.setStyleSheet('color: #2196F3; border: 1px solid #2196F3; padding: 4px; border-radius: 3px;')
        self.expand_collapse_btn.clicked.connect(self._toggle_expand_collapse)
        self._is_expanded = False  # Track expansion state
        tree_controls_l.addWidget(self.expand_collapse_btn)
        
        # Select all checkbox
        self.select_all_chk = QCheckBox('Select All')
        self.select_all_chk.setStyleSheet('color: #2196F3; font-weight: bold; margin-left: 12px;')
        self.select_all_chk.toggled.connect(self._on_select_all_toggled)
        tree_controls_l.addWidget(self.select_all_chk)
        
        tree_controls_l.addStretch()
        tree_controls.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        tree_container_l.addWidget(tree_controls)
        
        # Tree widget
        self.character_tree = QTreeWidget()
        self.character_tree.setHeaderHidden(True)
        self.character_tree.setMaximumWidth(400)  # Limit width to leave space on right
        self.character_tree.setMinimumHeight(200)
        # Remove maximum height to allow vertical expansion
        self.character_tree.itemChanged.connect(self._on_tree_item_changed)
        tree_container_l.addWidget(self.character_tree)
        
        tree_container.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        tree_section_l.addWidget(tree_container)
        
        # Right side: Copy preview and actions
        copy_actions = QWidget()
        copy_actions.setAttribute(Qt.WA_StyledBackground, False)
        copy_actions_l = QVBoxLayout(copy_actions)
        copy_actions_l.setContentsMargins(8, 0, 8, 0)
        
        # Copy preview section
        preview_scroll = QScrollArea()
        preview_scroll.setWidgetResizable(True)
        preview_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        preview_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        preview_scroll.setMinimumHeight(200)
        # Remove maximum height to allow growth with window
        preview_scroll.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        
        preview_container = QWidget()
        preview_container.setAttribute(Qt.WA_StyledBackground, True)
        preview_container.setStyleSheet('background: #f9f9f9; border: 1px solid #ddd; border-radius: 4px;')
        preview_container_l = QVBoxLayout(preview_container)
        preview_container_l.setContentsMargins(8, 8, 8, 8)
        
        # Preview header
        preview_header = QLabel('Copy Preview')
        preview_header.setStyleSheet('font-weight: bold; color: #333; font-size: 14px; margin-bottom: 8px;')
        preview_container_l.addWidget(preview_header)
        
        # Copy From section
        self.copy_from_label = QLabel('Copy From:')
        self.copy_from_label.setStyleSheet('font-weight: bold; color: #666; margin-top: 4px;')
        preview_container_l.addWidget(self.copy_from_label)
        
        self.copy_from_details = QLabel('No source selected')
        self.copy_from_details.setStyleSheet('margin-left: 12px; margin-bottom: 8px; color: #888;')
        self.copy_from_details.setWordWrap(True)
        preview_container_l.addWidget(self.copy_from_details)
        
        # Copy To section
        self.copy_to_label = QLabel('Copy To:')
        self.copy_to_label.setStyleSheet('font-weight: bold; color: #666; margin-top: 4px;')
        preview_container_l.addWidget(self.copy_to_label)
        
        self.copy_to_details = QLabel('No destinations selected')
        self.copy_to_details.setStyleSheet('margin-left: 12px; margin-bottom: 8px; color: #888;')
        self.copy_to_details.setWordWrap(True)
        preview_container_l.addWidget(self.copy_to_details)
        
        # Files section
        self.files_label = QLabel('Files & Folders:')
        self.files_label.setStyleSheet('font-weight: bold; color: #666; margin-top: 4px;')
        preview_container_l.addWidget(self.files_label)
        
        self.files_details = QLabel('No operations')
        self.files_details.setStyleSheet('margin-left: 12px; font-family: monospace; color: #888;')
        self.files_details.setWordWrap(True)
        preview_container_l.addWidget(self.files_details)
        
        # Add stretch to push content to top of scroll area
        preview_container_l.addStretch()
        
        # Set the preview container as the scroll area's widget
        preview_scroll.setWidget(preview_container)
        
        copy_actions_l.addWidget(preview_scroll)
        
        # Copy button
        self.copy_btn = QPushButton('Copy Settings')
        self.copy_btn.setMinimumWidth(120)
        self.copy_btn.setMinimumHeight(40)
        self.copy_btn.setStyleSheet('QPushButton { background-color: #2196F3; color: white; font-weight: bold; border: none; border-radius: 4px; margin-top: 8px; } QPushButton:hover { background-color: #1976D2; } QPushButton:disabled { background-color: #ccc; }')
        self.copy_btn.clicked.connect(self._copy_settings)
        copy_actions_l.addWidget(self.copy_btn)
        
        # Status label
        self.copy_status = QLabel('')
        self.copy_status.setWordWrap(True)
        self.copy_status.setStyleSheet('padding: 8px; background: #f5f5f5; border-radius: 4px; margin-top: 8px;')
        copy_actions_l.addWidget(self.copy_status)
        
        # Don't add stretch - let preview area expand instead
        copy_actions.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        copy_actions.setMinimumWidth(320)  # Slightly larger to accommodate scroll bar
        copy_actions.setMaximumWidth(400)  # Prevent excessive width
        tree_section_l.addWidget(copy_actions)
        
        tree_section.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.layout.addWidget(tree_section)

        # internal list of (name, id) for search
        self._char_map = {}  # map name -> cid
        
        # Status tracking variables
        self._account_file_exists = False
        self._character_file_exists = False
        self._current_character_id = None
        self._current_account_id = None
        
        self.reload()
        # Don't populate profiles on startup - let user select server first
        self.profile_combo.addItem('-- Select Server First --', None)
        self.dest_profile_combo.addItem('-- Select Server First --', None)
        self._update_file_status()  # Initial status check
        self._populate_character_tree()  # populate character tree
        self._update_copy_preview()  # Initial preview update

        # Allow the main widget to expand vertically to fill available space
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

    def _on_server_changed(self, idx: int):
        """Called when server selection changes."""
        self._populate_profiles()
        self._update_file_status()  # Check status after server change
        self._update_copy_preview()
    
    def _on_profile_changed(self, idx: int):
        """Called when profile selection changes."""
        self._update_file_status()  # Check status after profile change
        self._update_copy_preview()
    
    def _on_dest_server_changed(self, idx: int):
        """Called when destination server selection changes."""
        self._populate_dest_profiles()
        self._check_profile_exists()  # Recheck profile existence on server change
        self._update_copy_preview()
    
    def _on_dest_profile_changed(self, idx: int):
        """Called when destination profile selection changes."""
        self._update_copy_preview()
    
    def _on_new_profile_toggled(self, checked: bool):
        """Called when new profile checkbox is toggled."""
        if checked:
            # Disable dropdown, enable input field
            self.dest_profile_combo.setEnabled(False)
            self.new_profile_input.setEnabled(True)
            self.new_profile_input.setFocus()  # Focus on input field
            self._check_profile_exists()  # Check if current text conflicts
        else:
            # Enable dropdown, disable input field
            self.dest_profile_combo.setEnabled(True)
            self.new_profile_input.setEnabled(False)
            self.new_profile_input.clear()  # Clear any entered text
            self.profile_warning.setVisible(False)  # Hide warning
        self._update_copy_preview()
    
    def _on_new_profile_text_changed(self, text: str):
        """Called when new profile name text changes."""
        if self.new_profile_chk.isChecked():
            self._check_profile_exists()
        self._update_copy_preview()
    
    def _check_profile_exists(self):
        """Check if the entered profile name already exists and show warning (case-insensitive)."""
        if not self.new_profile_chk.isChecked():
            self.profile_warning.setVisible(False)
            return
            
        profile_name = self.new_profile_input.text().strip()
        if not profile_name:
            self.profile_warning.setVisible(False)
            return
            
        # Check if profile exists (case-insensitive for Windows compatibility)
        server_path = self.dest_server_combo.currentData()
        if not server_path:
            self.profile_warning.setVisible(False)
            return
            
        try:
            if self.mappings_path.exists():
                data = json.loads(self.mappings_path.read_text())
                dat_roots = data.get('dat_roots', [])
                if dat_roots:
                    base_path = Path(dat_roots[0])
                    server_dir = base_path / server_path
                    
                    if server_dir.exists():
                        # Get all existing profile directories and check case-insensitively
                        existing_profiles = []
                        for settings_dir in server_dir.glob('settings_*'):
                            if settings_dir.is_dir() and settings_dir.name != 'cache':
                                # Remove "settings_" prefix to get profile name
                                existing_name = settings_dir.name[9:]
                                if existing_name:
                                    existing_profiles.append(existing_name.lower())
                        
                        # Check if entered name conflicts case-insensitively
                        if profile_name.lower() in existing_profiles:
                            self.profile_warning.setVisible(True)
                        else:
                            self.profile_warning.setVisible(False)
                    else:
                        self.profile_warning.setVisible(False)
                else:
                    self.profile_warning.setVisible(False)
            else:
                self.profile_warning.setVisible(False)
        except Exception:
            self.profile_warning.setVisible(False)
    
    def _toggle_expand_collapse(self):
        """Toggle between expand all and collapse all."""
        if self._is_expanded:
            self.character_tree.collapseAll()
            self.expand_collapse_btn.setText('Expand All')
            self._is_expanded = False
        else:
            self.character_tree.expandAll()
            self.expand_collapse_btn.setText('Collapse All')
            self._is_expanded = True
    
    def _on_select_all_toggled(self, checked: bool):
        """Handle select all checkbox toggle."""
        # Temporarily disconnect to avoid recursion
        self.character_tree.itemChanged.disconnect(self._on_tree_item_changed)
        
        try:
            root = self.character_tree.invisibleRootItem()
            check_state = Qt.Checked if checked else Qt.Unchecked
            
            # Update all account and character items
            for i in range(root.childCount()):
                account_item = root.child(i)
                account_item.setCheckState(0, check_state)
                
                # Update all character items under this account
                for j in range(account_item.childCount()):
                    char_item = account_item.child(j)
                    char_item.setCheckState(0, check_state)
        finally:
            # Reconnect the signal
            self.character_tree.itemChanged.connect(self._on_tree_item_changed)
            # Update preview after changes
            self._update_copy_preview()
    
    def _populate_character_tree(self):
        """Populate the character tree with accounts and characters from mappings.json."""
        self.character_tree.clear()
        
        try:
            if not self.mappings_path.exists():
                return
                
            data = json.loads(self.mappings_path.read_text())
            mappings = data.get('mappings', {})
            
            for account_id, info in sorted(mappings.items(), key=lambda x: int(x[0])):
                # Create account node
                account_item = QTreeWidgetItem(self.character_tree)
                account_item.setText(0, f"Account {account_id}")
                account_item.setFlags(account_item.flags() | Qt.ItemIsUserCheckable)
                account_item.setCheckState(0, Qt.Unchecked)
                account_item.setData(0, Qt.UserRole, {'type': 'account', 'id': account_id})
                
                # Add character nodes
                char_ids = info.get('chars', [])
                for char_id in sorted(char_ids, key=lambda x: int(str(x))):
                    char_name = self._get_character_name(str(char_id))
                    
                    char_item = QTreeWidgetItem(account_item)
                    char_item.setText(0, char_name)
                    char_item.setFlags(char_item.flags() | Qt.ItemIsUserCheckable)
                    char_item.setCheckState(0, Qt.Unchecked)
                    char_item.setData(0, Qt.UserRole, {
                        'type': 'character', 
                        'id': str(char_id), 
                        'account_id': account_id
                    })
                
                # Collapse by default
                self.character_tree.collapseItem(account_item)
                
        except Exception as e:
            print(f"Error populating character tree: {e}")
    
    def _get_character_name(self, char_id: str) -> str:
        """Get character name from cache, fallback to ID if not found."""
        try:
            char_file = self.cache.base / 'char' / f'{char_id}.json'
            if char_file.exists():
                data = json.loads(char_file.read_text())
                return data.get('name', char_id)
        except Exception:
            pass
        return char_id
    
    def _on_tree_item_changed(self, item: QTreeWidgetItem, column: int):
        """Handle checkbox changes in the character tree."""
        if column != 0:
            return
            
        # Temporarily disconnect to avoid recursion
        self.character_tree.itemChanged.disconnect(self._on_tree_item_changed)
        
        try:
            item_data = item.data(0, Qt.UserRole)
            if not item_data:
                return
                
            if item_data['type'] == 'account':
                # Account checkbox changed - update all children
                check_state = item.checkState(0)
                for i in range(item.childCount()):
                    child = item.child(i)
                    child.setCheckState(0, check_state)
                    
            elif item_data['type'] == 'character':
                # Character checkbox changed - update parent if necessary
                parent = item.parent()
                if parent:
                    self._update_account_checkbox(parent)
        finally:
            # Reconnect the signal
            self.character_tree.itemChanged.connect(self._on_tree_item_changed)
            # Update preview after tree changes
            self._update_copy_preview()
            # Update select all checkbox state
            self._update_select_all_checkbox()
    
    def _update_account_checkbox(self, account_item: QTreeWidgetItem):
        """Update account checkbox state based on children."""
        total_children = account_item.childCount()
        checked_children = 0
        
        for i in range(total_children):
            child = account_item.child(i)
            if child.checkState(0) == Qt.Checked:
                checked_children += 1
        
        # Set account checkbox state
        if checked_children == 0:
            account_item.setCheckState(0, Qt.Unchecked)
        elif checked_children == total_children:
            account_item.setCheckState(0, Qt.Checked)
        else:
            account_item.setCheckState(0, Qt.PartiallyChecked)
    
    def _update_select_all_checkbox(self):
        """Update select all checkbox based on tree selection state."""
        root = self.character_tree.invisibleRootItem()
        total_chars = 0
        selected_chars = 0
        
        for i in range(root.childCount()):
            account_item = root.child(i)
            for j in range(account_item.childCount()):
                char_item = account_item.child(j)
                total_chars += 1
                if char_item.checkState(0) == Qt.Checked:
                    selected_chars += 1
        
        # Temporarily disconnect to avoid recursion
        self.select_all_chk.toggled.disconnect(self._on_select_all_toggled)
        
        try:
            if selected_chars == 0:
                self.select_all_chk.setCheckState(Qt.Unchecked)
            elif selected_chars == total_chars:
                self.select_all_chk.setCheckState(Qt.Checked)
            else:
                self.select_all_chk.setCheckState(Qt.PartiallyChecked)
        finally:
            # Reconnect the signal
            self.select_all_chk.toggled.connect(self._on_select_all_toggled)
    
    def _populate_profiles(self):
        """Populate the profile dropdown based on selected server.
        Profiles are dynamic and user-specific, so we scan fresh each time."""
        self.profile_combo.clear()
        
        server_path = self.server_combo.currentData()
        if not server_path:
            self.profile_combo.addItem("-- Select Server First --", None)
            return
            
        # Add blank option first to require explicit selection
        self.profile_combo.addItem("-- Select Profile --", None)
            
        try:
            # Get the dat_roots from mappings.json
            if not self.mappings_path.exists():
                self.profile_combo.addItem("No mappings.json found", None)
                return
                
            data = json.loads(self.mappings_path.read_text())
            dat_roots = data.get('dat_roots', [])
            
            if not dat_roots:
                self.profile_combo.addItem("No EVE directory configured", None)
                return
                
            base_path = Path(dat_roots[0])
            server_dir = base_path / server_path
            
            if not server_dir.exists():
                self.profile_combo.addItem(f"Server directory not found", None)
                return
            
            # Find all directories starting with "settings_" (excluding cache)
            profile_dirs = []
            for settings_dir in server_dir.glob('settings_*'):
                if settings_dir.is_dir() and settings_dir.name != 'cache':
                    profile_dirs.append(settings_dir)
            
            if not profile_dirs:
                self.profile_combo.addItem("No profiles found", None)
                return
            
            # Sort and add profiles
            for settings_dir in sorted(profile_dirs, key=lambda x: x.name):
                # Remove "settings_" prefix to get profile name
                profile_name = settings_dir.name[9:]  # Remove "settings_" (9 chars)
                if profile_name:  # Make sure we have a name after removing prefix
                    self.profile_combo.addItem(profile_name, settings_dir.name)
                    
        except Exception as e:
            print(f"Error populating profiles: {e}")
            self.profile_combo.addItem(f"Error: {str(e)}", None)
    
    def refresh_profiles(self):
        """Manually refresh the profile list. Call this if profiles might have changed."""
        self._populate_profiles()
        self._populate_dest_profiles()
    
    def _populate_dest_profiles(self):
        """Populate the destination profile dropdown based on selected server.
        Profiles are dynamic and user-specific, so we scan fresh each time."""
        self.dest_profile_combo.clear()
        
        server_path = self.dest_server_combo.currentData()
        if not server_path:
            self.dest_profile_combo.addItem("-- Select Server First --", None)
            return
            
        # Add blank option first to require explicit selection
        self.dest_profile_combo.addItem("-- Select Profile --", None)
            
        try:
            # Get the dat_roots from mappings.json
            if not self.mappings_path.exists():
                self.dest_profile_combo.addItem("No mappings.json found", None)
                return
                
            data = json.loads(self.mappings_path.read_text())
            dat_roots = data.get('dat_roots', [])
            
            if not dat_roots:
                self.dest_profile_combo.addItem("No EVE directory configured", None)
                return
                
            base_path = Path(dat_roots[0])
            server_dir = base_path / server_path
            
            if not server_dir.exists():
                self.dest_profile_combo.addItem(f"Server directory not found", None)
                return
            
            # Find all directories starting with "settings_" (excluding cache)
            profile_dirs = []
            for settings_dir in server_dir.glob('settings_*'):
                if settings_dir.is_dir() and settings_dir.name != 'cache':
                    profile_dirs.append(settings_dir)
            
            if not profile_dirs:
                self.dest_profile_combo.addItem("No profiles found", None)
                return
            
            # Sort and add profiles
            for settings_dir in sorted(profile_dirs, key=lambda x: x.name):
                # Remove "settings_" prefix to get profile name
                profile_name = settings_dir.name[9:]  # Remove "settings_" (9 chars)
                if profile_name:  # Make sure we have a name after removing prefix
                    self.dest_profile_combo.addItem(profile_name, settings_dir.name)
                    
        except Exception as e:
            print(f"Error populating destination profiles: {e}")
            self.dest_profile_combo.addItem(f"Error: {str(e)}", None)
    
    def _update_file_status(self):
        """Check if the required data files exist and update status indicators."""
        # Reset status
        self._account_file_exists = False
        self._character_file_exists = False
        
        profile_path = self.get_selected_profile_path()
        if not profile_path or not profile_path.exists():
            self._set_status_indicators(False, False)
            return
        
        # Check account file
        if self._current_account_id:
            account_file = profile_path / f"core_user_{self._current_account_id}.dat"
            self._account_file_exists = account_file.exists()
        
        # Check character file
        if self._current_character_id:
            char_file = profile_path / f"core_char_{self._current_character_id}.dat"
            self._character_file_exists = char_file.exists()
        
        self._set_status_indicators(self._account_file_exists, self._character_file_exists)
    
    def _set_status_indicators(self, account_exists: bool, character_exists: bool):
        """Update the visual status indicators."""
        # Green if exists, red if doesn't exist, gray if unknown
        account_color = '#4CAF50' if account_exists else '#f44336'  # Green or red
        char_color = '#4CAF50' if character_exists else '#f44336'    # Green or red
        
        if not self._current_account_id:
            account_color = '#ccc'  # Gray if no account selected
        if not self._current_character_id:
            char_color = '#ccc'     # Gray if no character selected
            
        self.account_indicator.setStyleSheet(f'color:{account_color}; font-size:12px; padding-right:8px;')
        self.char_indicator.setStyleSheet(f'color:{char_color}; font-size:12px; padding-right:8px;')
    
    def get_account_file_exists(self) -> bool:
        """Return whether the account data file exists."""
        return self._account_file_exists
    
    def get_character_file_exists(self) -> bool:
        """Return whether the character data file exists."""
        return self._character_file_exists
    
    def get_current_account_id(self) -> str:
        """Return the currently selected account ID."""
        return self._current_account_id
    
    def get_current_character_id(self) -> str:
        """Return the currently selected character ID."""
        return self._current_character_id
    
    def get_selected_server(self):
        """Get the currently selected server path."""
        return self.server_combo.currentData()
    
    def get_selected_profile(self):
        """Get the currently selected profile folder name.
        Returns None if no valid profile is selected."""
        data = self.profile_combo.currentData()
        return data if data is not None else None
    
    def get_selected_profile_path(self):
        """Get the full path to the selected profile directory.
        Returns None if no valid profile is selected."""
        server_path = self.get_selected_server()
        profile_name = self.get_selected_profile()
        
        if not server_path or not profile_name:
            return None
            
        try:
            if self.mappings_path.exists():
                data = json.loads(self.mappings_path.read_text())
                dat_roots = data.get('dat_roots', [])
                if dat_roots:
                    base_path = Path(dat_roots[0])
                    return base_path / server_path / profile_name
        except Exception:
            pass
        return None
    
    def get_selected_dest_server(self):
        """Get the currently selected destination server path."""
        return self.dest_server_combo.currentData()
    
    def get_selected_dest_profile(self):
        """Get the currently selected destination profile folder name.
        Returns None if no valid profile is selected."""
        if self.new_profile_chk.isChecked():
            # Return new profile name if creating new profile
            new_name = self.new_profile_input.text().strip()
            return f"settings_{new_name}" if new_name else None
        else:
            # Return selected existing profile
            data = self.dest_profile_combo.currentData()
            return data if data is not None else None
    
    def get_new_profile_name(self):
        """Get the new profile name entered by user (without settings_ prefix).
        Returns None if not creating new profile or name is empty."""
        if self.new_profile_chk.isChecked():
            return self.new_profile_input.text().strip() or None
        return None
    
    def is_creating_new_profile(self):
        """Return whether user is creating a new profile."""
        return self.new_profile_chk.isChecked()
    
    def has_profile_name_conflict(self):
        """Return whether the new profile name conflicts with existing profile (case-insensitive)."""
        if not self.new_profile_chk.isChecked():
            return False
            
        profile_name = self.new_profile_input.text().strip()
        if not profile_name:
            return False
            
        # Check if profile exists case-insensitively (for Windows compatibility)
        server_path = self.dest_server_combo.currentData()
        if not server_path:
            return False
            
        try:
            if self.mappings_path.exists():
                data = json.loads(self.mappings_path.read_text())
                dat_roots = data.get('dat_roots', [])
                if dat_roots:
                    base_path = Path(dat_roots[0])
                    server_dir = base_path / server_path
                    
                    if server_dir.exists():
                        # Get all existing profile directories and check case-insensitively
                        existing_profiles = []
                        for settings_dir in server_dir.glob('settings_*'):
                            if settings_dir.is_dir() and settings_dir.name != 'cache':
                                # Remove "settings_" prefix to get profile name
                                existing_name = settings_dir.name[9:]
                                if existing_name:
                                    existing_profiles.append(existing_name.lower())
                        
                        # Check if entered name conflicts case-insensitively
                        return profile_name.lower() in existing_profiles
        except Exception:
            pass
        return False
    
    def get_selected_characters(self) -> list:
        """Get list of selected character IDs from the tree."""
        selected_chars = []
        
        root = self.character_tree.invisibleRootItem()
        for i in range(root.childCount()):
            account_item = root.child(i)
            for j in range(account_item.childCount()):
                char_item = account_item.child(j)
                if char_item.checkState(0) == Qt.Checked:
                    item_data = char_item.data(0, Qt.UserRole)
                    if item_data and item_data['type'] == 'character':
                        selected_chars.append(item_data['id'])
        
        return selected_chars
    
    def get_selected_accounts(self) -> list:
        """Get list of selected account IDs from the tree."""
        selected_accounts = []
        
        root = self.character_tree.invisibleRootItem()
        for i in range(root.childCount()):
            account_item = root.child(i)
            if account_item.checkState(0) == Qt.Checked:
                item_data = account_item.data(0, Qt.UserRole)
                if item_data and item_data['type'] == 'account':
                    selected_accounts.append(item_data['id'])
        
        return selected_accounts
    
    def get_selected_character_details(self) -> list:
        """Get detailed list of selected characters with account info."""
        selected_details = []
        
        root = self.character_tree.invisibleRootItem()
        for i in range(root.childCount()):
            account_item = root.child(i)
            for j in range(account_item.childCount()):
                char_item = account_item.child(j)
                if char_item.checkState(0) == Qt.Checked:
                    item_data = char_item.data(0, Qt.UserRole)
                    if item_data and item_data['type'] == 'character':
                        selected_details.append({
                            'character_id': item_data['id'],
                            'character_name': char_item.text(0),
                            'account_id': item_data['account_id']
                        })
        
        return selected_details
    
    def get_selected_dest_profile_path(self):
        """Get the full path to the selected destination profile directory.
        Returns None if no valid profile is selected."""
        server_path = self.get_selected_dest_server()
        profile_name = self.get_selected_dest_profile()
        
        if not server_path or not profile_name:
            return None
            
        try:
            if self.mappings_path.exists():
                data = json.loads(self.mappings_path.read_text())
                dat_roots = data.get('dat_roots', [])
                if dat_roots:
                    base_path = Path(dat_roots[0])
                    profile_path = base_path / server_path / profile_name
                    
                    # If creating new profile, the path may not exist yet
                    if self.is_creating_new_profile():
                        # Return the path where the new profile would be created
                        return profile_path
                    else:
                        # Only return existing profile paths
                        return profile_path if profile_path.exists() else None
        except Exception:
            pass
        return None

    def _on_completer_activated(self, text: str):
        """Called when user selects a character from the completer popup."""
        cid = self._char_map.get(text)
        if cid:
            self._on_char_selected(cid)

    def _on_search_text(self, text: str):
        # deprecated: old popup handler, kept for compatibility
        pass

    def _on_popup_clicked(self, item: 'QListWidgetItem'):
        # deprecated: old popup handler, kept for compatibility
        pass

    def reload(self):
        """Reload both character list and profiles (since both can change dynamically)."""
        # list all cached char JSONs and populate completer with 'Full Name'
        self._char_map.clear()
        chars_dir = self.cache.base / 'char'
        names = []
        if chars_dir.exists():
            for p in sorted(chars_dir.glob('*.json')):
                cid = p.stem
                try:
                    data = json.loads(p.read_text())
                    name = data.get('name') or f'{cid}'
                except Exception:
                    name = f'{cid}'
                names.append(name)
                self._char_map[name] = cid
        # update completer model
        self._model.setStringList(sorted(names, key=lambda x: x.lower()))
        
        # Also refresh profiles since they can change
        self._populate_profiles()
        # Update status after reload
        self._update_file_status()

    def _on_char_changed(self, idx: int):
        if idx < 0:
            self.account_label.setText('')
            return
        cid = self.char_combo.itemData(idx)
        # find account from mappings.json that contains this char
        account = None
        try:
            if self.mappings_path.exists():
                data = json.loads(self.mappings_path.read_text())
                for acc, info in data.get('mappings', {}).items():
                    if str(cid) in [str(x) for x in info.get('chars', [])]:
                        account = acc
                        break
        except Exception:
            account = None
        if account is not None:
            self.account_label.setText(f'Account {account}')
        else:
            self.account_label.setText('Account —')

    def _on_char_selected(self, cid: str):
        """Update account label when a character is selected from the popup."""
        self._current_character_id = cid
        account = None
        try:
            if self.mappings_path.exists():
                data = json.loads(self.mappings_path.read_text())
                for acc, info in data.get('mappings', {}).items():
                    if str(cid) in [str(x) for x in info.get('chars', [])]:
                        account = acc
                        self._current_account_id = acc
                        break
        except Exception:
            account = None
            self._current_account_id = None
        
        if account is not None:
            self.account_label.setText(f'Account {account}')
        else:
            self.account_label.setText('Account —')
            
        # Update file status and preview after character selection
        self._update_file_status()
        self._update_copy_preview()
            
        # Update file status and preview after character selection
        self._update_file_status()
        self._update_copy_preview()
    
    def _on_account_config_toggled(self, checked: bool):
        """Called when account config checkbox is toggled."""
        self._update_copy_preview()
    
    def _on_char_input_finished(self):
        """Called when character input editing is finished (focus lost or Enter pressed)."""
        # Try to match the current text to a character
        current_text = self.char_search.text().strip()
        if current_text and current_text in self._char_map:
            cid = self._char_map[current_text]
            self._on_char_selected(cid)
            
    def _copy_settings(self):
        """Copy settings according to the defined logic."""
        try:
            # Validate inputs
            if not self._current_character_id:
                self._set_copy_status("Please select a source character", "error")
                return
                
            selected_chars = self.get_selected_characters()
            if not selected_chars:
                self._set_copy_status("Please select destination characters", "error")
                return
                
            source_profile_path = self.get_selected_profile_path()
            if not source_profile_path or not source_profile_path.exists():
                self._set_copy_status("Source profile not found", "error")
                return
                
            # Get destination profile path
            dest_profile_path = self.get_selected_dest_profile_path()
            if not dest_profile_path:
                self._set_copy_status("Invalid destination profile", "error")
                return
                
            # Check for profile conflicts if creating new profile
            if self.is_creating_new_profile() and self.has_profile_name_conflict():
                self._set_copy_status("Profile name already exists", "error")
                return
                
            # SCENARIO 3: Handle new profile creation
            if self.is_creating_new_profile():
                success = self._create_new_profile_with_templates(source_profile_path, dest_profile_path)
                if not success:
                    return
                    
            # CHECK A: Get donor account ID
            donor_account_id = self._current_account_id
            if not donor_account_id:
                self._set_copy_status("Could not determine source account", "error")
                return
                
            # Get source character file
            source_char_file = source_profile_path / f"core_char_{self._current_character_id}.dat"
            if not source_char_file.exists():
                self._set_copy_status(f"Source character file not found: {source_char_file.name}", "error")
                return
                
            copied_files = []
            use_account_config = self.use_account_cfg_chk.isChecked()
            
            # Process each selected destination character
            for char_id in selected_chars:
                # CHECK B: Get receiving character's account ID
                receiving_account_id = self._get_account_id_for_character(char_id)
                if not receiving_account_id:
                    self._set_copy_status(f"Could not determine account for character {char_id}", "error")
                    return
                    
                # Copy character file
                dest_char_file = dest_profile_path / f"core_char_{char_id}.dat"
                
                # Skip copying if source and destination are the same file
                if source_char_file.resolve() == dest_char_file.resolve():
                    # Silently skip - user selected source character as destination
                    pass
                else:
                    try:
                        shutil.copy2(source_char_file, dest_char_file)
                        copied_files.append(f"core_char_{char_id}.dat")
                    except Exception as e:
                        self._set_copy_status(f"Error copying character file for {char_id}: {str(e)}", "error")
                        return
                    
                # Handle account file (CHECK C with modifications)
                dest_account_file = dest_profile_path / f"core_user_{receiving_account_id}.dat"
                source_account_file = source_profile_path / f"core_user_{donor_account_id}.dat"
                
                if source_account_file.exists():
                    should_copy_account = False
                    
                    if use_account_config:
                        # Always copy/overwrite if "Use account config as well" is checked
                        should_copy_account = True
                    elif not dest_account_file.exists():
                        # Copy only if destination account file doesn't exist
                        should_copy_account = True
                        
                    if should_copy_account:
                        # Skip copying if source and destination are the same file
                        if source_account_file.resolve() == dest_account_file.resolve():
                            # Silently skip - same account file
                            pass
                        else:
                            try:
                                shutil.copy2(source_account_file, dest_account_file)
                                if f"core_user_{receiving_account_id}.dat" not in copied_files:
                                    copied_files.append(f"core_user_{receiving_account_id}.dat")
                            except Exception as e:
                                self._set_copy_status(f"Error copying account file for {receiving_account_id}: {str(e)}", "error")
                                return
                            
            # Success message
            char_count = len(selected_chars)
            file_count = len(copied_files)
            message = f"Successfully copied {file_count} files to {char_count} character(s)"
            if self.is_creating_new_profile():
                message += f" in new profile '{self.get_new_profile_name()}'"
            self._set_copy_status(message, "success")
            
        except Exception as e:
            self._set_copy_status(f"Unexpected error: {str(e)}", "error")
    
    def _create_new_profile_with_templates(self, source_profile_path: Path, dest_profile_path: Path) -> bool:
        """Create new profile directory and copy template files."""
        try:
            # Create the new profile directory
            dest_profile_path.mkdir(parents=True, exist_ok=True)
            
            # Template files to copy from source profile
            template_files = [
                "core_char__.dat",
                "core_char_('char', None, 'dat').dat", 
                "core_user__.dat",
                "core_public__.yaml",
                "prefs.ini"
            ]
            
            copied_templates = []
            for template_file in template_files:
                source_file = source_profile_path / template_file
                dest_file = dest_profile_path / template_file
                
                if source_file.exists():
                    try:
                        shutil.copy2(source_file, dest_file)
                        copied_templates.append(template_file)
                    except Exception as e:
                        self._set_copy_status(f"Error copying template {template_file}: {str(e)}", "error")
                        return False
                        
            self._set_copy_status(f"Created new profile with {len(copied_templates)} template files", "info")
            return True
            
        except Exception as e:
            self._set_copy_status(f"Error creating new profile: {str(e)}", "error")
            return False
    
    def _get_account_id_for_character(self, char_id: str) -> str:
        """Get account ID for a given character ID from mappings."""
        try:
            if self.mappings_path.exists():
                data = json.loads(self.mappings_path.read_text())
                for account_id, info in data.get('mappings', {}).items():
                    if str(char_id) in [str(x) for x in info.get('chars', [])]:
                        return account_id
        except Exception:
            pass
        return None
    
    def _set_copy_status(self, message: str, status_type: str = "info"):
        """Set copy status message with appropriate styling."""
        color_map = {
            "success": "#4CAF50",
            "error": "#f44336", 
            "info": "#2196F3",
            "warning": "#FF9800"
        }
        
        color = color_map.get(status_type, "#666")
        self.copy_status.setText(message)
        self.copy_status.setStyleSheet(f'padding: 8px; background: #f5f5f5; border-left: 4px solid {color}; border-radius: 4px; color: {color};')
        
        # Also print to console for debugging
        print(f"[{status_type.upper()}] {message}")
    
    def _update_copy_preview(self):
        """Update the copy preview panel with current selections."""
        try:
            # Update Copy From section
            if self._current_character_id and self._current_account_id:
                char_name = self._get_character_name_by_id(self._current_character_id)
                source_profile = self.get_selected_profile() or "Unknown Profile"
                server_data = self.get_selected_server()
                source_server = "Main server" if server_data == 'c_ccp_eve_tq_tranquility' else "Test server" if server_data == 'c_ccp_eve_sisi_singularity' else "No server selected"
                
                copy_from_text = f"{char_name} (ID: {self._current_character_id})\n"
                copy_from_text += f"Account: {self._current_account_id}\n"
                copy_from_text += f"Server: {source_server}\n"
                copy_from_text += f"Profile: {source_profile}"
                
                if self.use_account_cfg_chk.isChecked():
                    copy_from_text += "\n✓ Include account config"
                    
                self.copy_from_details.setText(copy_from_text)
                self.copy_from_details.setStyleSheet('margin-left: 12px; margin-bottom: 8px; color: #333;')
            else:
                self.copy_from_details.setText('No source character selected')
                self.copy_from_details.setStyleSheet('margin-left: 12px; margin-bottom: 8px; color: #888;')
            
            # Update Copy To section
            selected_chars = self.get_selected_characters()
            if selected_chars:
                dest_server_data = self.get_selected_dest_server()
                dest_server_name = "Main server" if dest_server_data == 'c_ccp_eve_tq_tranquility' else "Test server" if dest_server_data == 'c_ccp_eve_sisi_singularity' else "No server selected"
                
                if self.is_creating_new_profile():
                    new_profile_name = self.get_new_profile_name()
                    copy_to_text = f"Server: {dest_server_name}\n"
                    copy_to_text += f"New Profile: {new_profile_name}\n\n"
                else:
                    dest_profile = self.get_selected_dest_profile()
                    if dest_profile and dest_profile.startswith('settings_'):
                        dest_profile = dest_profile[9:]  # Remove settings_ prefix
                    copy_to_text = f"Server: {dest_server_name}\n"
                    copy_to_text += f"Profile: {dest_profile}\n\n"
                
                copy_to_text += f"Characters ({len(selected_chars)}):"                
                for char_id in selected_chars:
                    char_name = self._get_character_name_by_id(char_id)
                    account_id = self._get_account_id_for_character(char_id)
                    copy_to_text += f"\n• {char_name} (Acc: {account_id})"
                    
                self.copy_to_details.setText(copy_to_text)
                self.copy_to_details.setStyleSheet('margin-left: 12px; margin-bottom: 8px; color: #333;')
            else:
                self.copy_to_details.setText('No destination characters selected')
                self.copy_to_details.setStyleSheet('margin-left: 12px; margin-bottom: 8px; color: #888;')
            
            # Update Files section
            if self._current_character_id and selected_chars:
                files_text = self._generate_files_preview()
                self.files_details.setText(files_text)
                self.files_details.setStyleSheet('margin-left: 12px; font-family: monospace; color: #333; font-size: 11px;')
                
                # Enable copy button
                self.copy_btn.setEnabled(True)
            else:
                self.files_details.setText('No operations to preview')
                self.files_details.setStyleSheet('margin-left: 12px; font-family: monospace; color: #888;')
                
                # Disable copy button
                self.copy_btn.setEnabled(False)
                
        except Exception as e:
            print(f"Error updating copy preview: {e}")
    
    def _get_character_name_by_id(self, char_id: str) -> str:
        """Get character name by ID, with fallback."""
        for name, cid in self._char_map.items():
            if cid == char_id:
                return name
        return self._get_character_name(char_id)  # Fallback to cache lookup
    
    def _generate_files_preview(self) -> str:
        """Generate preview of files that will be copied/created."""
        try:
            selected_chars = self.get_selected_characters()
            if not selected_chars or not self._current_character_id:
                return "No operations"
                
            files_text = ""
            
            # New profile template files
            if self.is_creating_new_profile():
                new_profile_name = self.get_new_profile_name()
                files_text += f"📁 Create: settings_{new_profile_name}/\n\n"
                
                template_files = [
                    "core_char__.dat",
                    "core_char_('char', None, 'dat').dat",
                    "core_user__.dat", 
                    "core_public__.yaml",
                    "prefs.ini"
                ]
                
                files_text += "Template files:\n"
                for template in template_files:
                    files_text += f"📄 Copy: {template}\n"
                files_text += "\n"
            
            # Character files
            files_text += "Character files:\n"
            for char_id in selected_chars:
                files_text += f"📄 Copy: core_char_{char_id}.dat\n"
            
            # Account files
            if selected_chars:
                files_text += "\nAccount files:\n"
                processed_accounts = set()
                
                for char_id in selected_chars:
                    account_id = self._get_account_id_for_character(char_id)
                    if account_id and account_id not in processed_accounts:
                        processed_accounts.add(account_id)
                        files_text += f"📄 Copy: core_user_{account_id}.dat\n"
            
            return files_text
            
        except Exception as e:
            return f"Error generating preview: {str(e)}"

