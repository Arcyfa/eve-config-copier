from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QTextEdit,
    QMessageBox,
    QTreeWidget,
    QTreeWidgetItem,
    QSizePolicy,
    QGroupBox,
    QSplitter,
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont
from pathlib import Path
import json
import shutil
import zipfile
from datetime import datetime
from typing import Optional
import os


class BackupWorker(QThread):
    """Background worker for backup operations."""
    progress = Signal(str)  # Progress message
    finished = Signal(bool, str)  # Success flag and result message
    
    def __init__(self, mappings_path: str, backup_dir: str):
        super().__init__()
        self.mappings_path = Path(mappings_path)
        self.backup_dir = Path(backup_dir)
    
    def run(self):
        try:
            self.progress.emit("Starting backup operation...")
            
            # Check if mappings.json exists
            if not self.mappings_path.exists():
                self.finished.emit(False, "mappings.json not found")
                return
            
            # Load mappings to get dat_roots
            data = json.loads(self.mappings_path.read_text())
            dat_roots = data.get('dat_roots', [])
            
            if not dat_roots:
                self.finished.emit(False, "No dat_roots configured in mappings.json")
                return
            
            # Create backup directory if it doesn't exist
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Create backup zip file with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"eve_backup_{timestamp}.zip"
            backup_path = self.backup_dir / backup_filename
            
            self.progress.emit(f"Creating backup archive: {backup_filename}")
            
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as backup_zip:
                # Process each dat_root
                for dat_root in dat_roots:
                    root_path = Path(dat_root)
                    if not root_path.exists():
                        self.progress.emit(f"Skipping non-existent path: {root_path}")
                        continue
                        
                    self.progress.emit(f"Processing EVE directory: {root_path}")
                    
                    # Backup main server directory (excluding cache)
                    main_server_dir = root_path / 'c_ccp_eve_tq_tranquility'
                    if main_server_dir.exists():
                        self.progress.emit("Backing up main server (Tranquility)...")
                        self._backup_server_directory(backup_zip, main_server_dir, 'c_ccp_eve_tq_tranquility')
                    
                    # Backup test server directory (excluding cache)
                    test_server_dir = root_path / 'c_ccp_eve_sisi_singularity'
                    if test_server_dir.exists():
                        self.progress.emit("Backing up test server (Singularity)...")
                        self._backup_server_directory(backup_zip, test_server_dir, 'c_ccp_eve_sisi_singularity')
            
            backup_size = backup_path.stat().st_size / (1024 * 1024)  # Size in MB
            self.finished.emit(True, f"Backup completed! File: {backup_filename} ({backup_size:.1f} MB)")
            
        except Exception as e:
            self.finished.emit(False, f"Backup failed: {str(e)}")
    
    def _backup_server_directory(self, backup_zip, server_dir: Path, server_name: str):
        """Backup a server directory excluding cache."""
        for item in server_dir.iterdir():
            if item.is_dir():
                # Skip cache directories
                if item.name == 'cache':
                    continue
                    
                # Backup profile directories (settings_*)
                if item.name.startswith('settings_'):
                    self.progress.emit(f"  Backing up profile: {item.name}")
                    for file_path in item.rglob('*'):
                        if file_path.is_file():
                            # Create archive path
                            rel_path = file_path.relative_to(server_dir)
                            arc_name = f"{server_name}/{rel_path}"
                            backup_zip.write(file_path, arc_name)
            elif item.is_file():
                # Backup any files in server root
                arc_name = f"{server_name}/{item.name}"
                backup_zip.write(item, arc_name)


class RestoreWorker(QThread):
    """Background worker for restore operations."""
    progress = Signal(str)  # Progress message
    finished = Signal(bool, str)  # Success flag and result message
    
    def __init__(self, backup_path: str, mappings_path: str, backup_dir: str):
        super().__init__()
        self.backup_path = Path(backup_path)
        self.mappings_path = Path(mappings_path)
        self.backup_dir = Path(backup_dir)
    
    def run(self):
        try:
            self.progress.emit("Starting restore operation...")
            
            if not self.backup_path.exists():
                self.finished.emit(False, "Backup file not found")
                return
            
            # Create safety backup before restore
            self.progress.emit("Creating safety backup before restore...")
            safety_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safety_backup_path = self.backup_dir / f"safety_backup_{safety_timestamp}.zip"
            
            # Create safety backup using same logic as regular backup
            safety_worker = BackupWorker(str(self.mappings_path), str(self.backup_dir))
            
            # Run safety backup synchronously
            if self.mappings_path.exists():
                data = json.loads(self.mappings_path.read_text())
                dat_roots = data.get('dat_roots', [])
                
                if dat_roots:
                    with zipfile.ZipFile(safety_backup_path, 'w', zipfile.ZIP_DEFLATED) as safety_zip:
                        for dat_root in dat_roots:
                            root_path = Path(dat_root)
                            if not root_path.exists():
                                continue
                                
                            main_server_dir = root_path / 'c_ccp_eve_tq_tranquility'
                            if main_server_dir.exists():
                                safety_worker._backup_server_directory(safety_zip, main_server_dir, 'c_ccp_eve_tq_tranquility')
                            
                            test_server_dir = root_path / 'c_ccp_eve_sisi_singularity'
                            if test_server_dir.exists():
                                safety_worker._backup_server_directory(safety_zip, test_server_dir, 'c_ccp_eve_sisi_singularity')
                    
                    self.progress.emit(f"Safety backup created: {safety_backup_path.name}")
            
            # Load mappings to get restore destinations
            if not self.mappings_path.exists():
                self.finished.emit(False, "mappings.json not found")
                return
                
            data = json.loads(self.mappings_path.read_text())
            dat_roots = data.get('dat_roots', [])
            
            if not dat_roots:
                self.finished.emit(False, "No dat_roots in mappings.json")
                return
            
            # Extract and restore backup
            self.progress.emit("Extracting and restoring backup...")
            
            with zipfile.ZipFile(self.backup_path, 'r') as backup_zip:
                file_list = backup_zip.namelist()
                
                # Group files by server
                main_server_files = [f for f in file_list if f.startswith('c_ccp_eve_tq_tranquility/')]
                test_server_files = [f for f in file_list if f.startswith('c_ccp_eve_sisi_singularity/')]
                
                # Restore to first available dat_root
                restore_root = Path(dat_roots[0])
                
                # Restore main server files
                if main_server_files:
                    self.progress.emit("Restoring main server files...")
                    for file_path in main_server_files:
                        # Remove server prefix to get relative path
                        rel_path = '/'.join(file_path.split('/')[1:])  # Remove 'c_ccp_eve_tq_tranquility'
                        if rel_path:  # Make sure there's a path after removing prefix
                            dest_path = restore_root / 'c_ccp_eve_tq_tranquility' / rel_path
                            dest_path.parent.mkdir(parents=True, exist_ok=True)
                            
                            with backup_zip.open(file_path) as source:
                                dest_path.write_bytes(source.read())
                
                # Restore test server files
                if test_server_files:
                    self.progress.emit("Restoring test server files...")
                    for file_path in test_server_files:
                        # Remove server prefix to get relative path
                        rel_path = '/'.join(file_path.split('/')[1:])  # Remove 'c_ccp_eve_sisi_singularity'
                        if rel_path:  # Make sure there's a path after removing prefix
                            dest_path = restore_root / 'c_ccp_eve_sisi_singularity' / rel_path
                            dest_path.parent.mkdir(parents=True, exist_ok=True)
                            
                            with backup_zip.open(file_path) as source:
                                dest_path.write_bytes(source.read())
            
            self.finished.emit(True, f"Restore completed! Safety backup: {safety_backup_path.name}")
            
        except Exception as e:
            self.finished.emit(False, f"Restore failed: {str(e)}")


class BackupTab(QWidget):
    def __init__(self, mappings_path: Optional[str] = None, parent=None):
        super().__init__(parent)
        self.mappings_path = Path(mappings_path) if mappings_path else Path.cwd() / 'mappings.json'
        self.backup_dir = Path.cwd() / 'backups'  # Backup folder in project directory
        self.layout = QVBoxLayout(self)
        
        # Title header
        header = QWidget()
        header.setAttribute(Qt.WA_StyledBackground, True)
        header.setStyleSheet('background:#eee; padding:2px;')
        header_l = QHBoxLayout(header)
        header_l.setContentsMargins(8, 2, 8, 2)
        header_label = QLabel('Backup and Restore EVE Server Directories')
        header_label.setStyleSheet('font-weight: bold; color:#222;')
        header_l.addWidget(header_label)
        header_l.addStretch()
        header.setFixedHeight(24)
        self.layout.addWidget(header)
        
        # Create splitter for top/bottom layout
        splitter = QSplitter(Qt.Vertical)
        
        # Top section: Create Backup
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(20, 10, 20, 10)
        
        # Create backup section
        backup_group = QGroupBox("Create Backup")
        backup_group.setStyleSheet('QGroupBox { font-weight: bold; padding-top: 10px; }')
        backup_layout = QVBoxLayout(backup_group)
        
        backup_desc = QLabel("Create a backup of both server directories (Tranquility & Singularity) excluding cache folders.")
        backup_desc.setWordWrap(True)
        backup_desc.setStyleSheet('color: #666; margin-bottom: 10px;')
        backup_layout.addWidget(backup_desc)
        
        # Backup button
        self.backup_btn = QPushButton("Create Backup Archive")
        self.backup_btn.setMinimumHeight(40)
        self.backup_btn.setStyleSheet('QPushButton { background-color: #2196F3; color: white; font-weight: bold; border: none; border-radius: 4px; padding: 8px 16px; } QPushButton:hover { background-color: #1976D2; } QPushButton:disabled { background-color: #ccc; }')
        self.backup_btn.clicked.connect(self._create_backup)
        backup_layout.addWidget(self.backup_btn)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        backup_layout.addWidget(self.progress_bar)
        
        top_layout.addWidget(backup_group)
        splitter.addWidget(top_widget)
        
        # Bottom section: Restore
        bottom_widget = QWidget()
        bottom_layout = QHBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(20, 10, 20, 20)
        
        # Left: Backup tree view
        tree_container = QWidget()
        tree_layout = QVBoxLayout(tree_container)
        tree_layout.setContentsMargins(0, 0, 0, 0)
        
        tree_label = QLabel("Available Backups:")
        tree_label.setStyleSheet('font-weight: bold; color:#222; margin-bottom: 5px;')
        tree_layout.addWidget(tree_label)
        
        self.backup_tree = QTreeWidget()
        self.backup_tree.setHeaderHidden(True)
        self.backup_tree.setMinimumWidth(300)
        self.backup_tree.setMaximumWidth(400)
        self.backup_tree.itemChanged.connect(self._on_tree_item_changed)
        tree_layout.addWidget(self.backup_tree)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh List")
        refresh_btn.clicked.connect(self._populate_backup_tree)
        refresh_btn.setMaximumWidth(100)
        tree_layout.addWidget(refresh_btn)
        
        bottom_layout.addWidget(tree_container)
        
        # Right: Restore controls and progress
        restore_container = QWidget()
        restore_layout = QVBoxLayout(restore_container)
        restore_layout.setContentsMargins(20, 0, 0, 0)
        
        # Restore section
        restore_group = QGroupBox("Restore Backup")
        restore_group.setStyleSheet('QGroupBox { font-weight: bold; padding-top: 10px; }')
        restore_group_layout = QVBoxLayout(restore_group)
        
        restore_desc = QLabel("Select a backup to restore. A safety backup will be created before restoring.")
        restore_desc.setWordWrap(True)
        restore_desc.setStyleSheet('color: #666; margin-bottom: 10px;')
        restore_group_layout.addWidget(restore_desc)
        
        # Warning
        warning = QLabel("⚠️ This will overwrite current EVE settings!")
        warning.setStyleSheet('color: #f44336; font-weight: bold; margin-bottom: 10px;')
        restore_group_layout.addWidget(warning)
        
        # Restore button
        self.restore_btn = QPushButton("Restore Selected Backup")
        self.restore_btn.setMinimumHeight(40)
        self.restore_btn.setStyleSheet('QPushButton { background-color: #FF9800; color: white; font-weight: bold; border: none; border-radius: 4px; padding: 8px 16px; } QPushButton:hover { background-color: #F57C00; } QPushButton:disabled { background-color: #ccc; }')
        self.restore_btn.clicked.connect(self._restore_backup)
        self.restore_btn.setEnabled(False)
        restore_group_layout.addWidget(self.restore_btn)
        
        restore_layout.addWidget(restore_group)
        
        # Progress log
        log_label = QLabel("Operation Log:")
        log_label.setStyleSheet('font-weight: bold; color:#222; margin-top: 20px; margin-bottom: 5px;')
        restore_layout.addWidget(log_label)
        
        self.progress_text = QTextEdit()
        self.progress_text.setMaximumHeight(200)
        self.progress_text.setReadOnly(True)
        self.progress_text.setStyleSheet('background: #f5f5f5; border: 1px solid #ddd; border-radius: 4px; padding: 4px; font-family: monospace; font-size: 11px; color: #333;')
        restore_layout.addWidget(self.progress_text)
        
        restore_layout.addStretch()
        bottom_layout.addWidget(restore_container)
        
        splitter.addWidget(bottom_widget)
        splitter.setSizes([200, 400])  # Give more space to bottom section
        
        self.layout.addWidget(splitter)
        
        # Thread management
        self._worker = None
        self._selected_backup = None
        
        # Initialize
        self._populate_backup_tree()
        
        # Allow tab to expand
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    
    def _create_backup(self):
        """Create a backup of server directories."""
        if self._worker and self._worker.isRunning():
            return
        
        # Start backup process
        self.progress_text.clear()
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.backup_btn.setEnabled(False)
        self.restore_btn.setEnabled(False)
        
        self._worker = BackupWorker(str(self.mappings_path), str(self.backup_dir))
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_backup_finished)
        self._worker.start()
    
    def _restore_backup(self):
        """Restore selected backup."""
        if not self._selected_backup:
            QMessageBox.warning(self, "No Selection", "Please select a backup to restore.")
            return
            
        if self._worker and self._worker.isRunning():
            return
        
        # Confirm with user
        reply = QMessageBox.question(
            self,
            "Confirm Restore",
            f"This will restore '{self._selected_backup}' and overwrite current EVE settings.\n\nA safety backup will be created first. Continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Start restore process
        backup_path = self.backup_dir / self._selected_backup
        self.progress_text.clear()
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.backup_btn.setEnabled(False)
        self.restore_btn.setEnabled(False)
        
        self._worker = RestoreWorker(str(backup_path), str(self.mappings_path), str(self.backup_dir))
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_restore_finished)
        self._worker.start()
    
    def _populate_backup_tree(self):
        """Populate the backup tree with available backups."""
        self.backup_tree.clear()
        self._selected_backup = None
        self.restore_btn.setEnabled(False)
        
        # Create backup directory if it doesn't exist
        self.backup_dir.mkdir(exist_ok=True)
        
        # Find all backup files
        backup_files = list(self.backup_dir.glob('*.zip'))
        backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)  # Newest first
        
        if not backup_files:
            no_backups_item = QTreeWidgetItem(self.backup_tree)
            no_backups_item.setText(0, "No backups found")
            no_backups_item.setFlags(no_backups_item.flags() & ~Qt.ItemIsEnabled)
            return
        
        for backup_file in backup_files:
            item = QTreeWidgetItem(self.backup_tree)
            
            # Format display name with size and date
            size_mb = backup_file.stat().st_size / (1024 * 1024)
            mod_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
            display_name = f"{backup_file.name} ({size_mb:.1f} MB) - {mod_time.strftime('%Y-%m-%d %H:%M')}"
            
            item.setText(0, display_name)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(0, Qt.Unchecked)
            item.setData(0, Qt.UserRole, backup_file.name)  # Store actual filename
    
    def _on_tree_item_changed(self, item: QTreeWidgetItem, column: int):
        """Handle checkbox changes - only allow single selection."""
        if column != 0:
            return
        
        # Temporarily disconnect to avoid recursion
        self.backup_tree.itemChanged.disconnect(self._on_tree_item_changed)
        
        try:
            if item.checkState(0) == Qt.Checked:
                # Uncheck all other items
                root = self.backup_tree.invisibleRootItem()
                for i in range(root.childCount()):
                    other_item = root.child(i)
                    if other_item != item:
                        other_item.setCheckState(0, Qt.Unchecked)
                
                # Set selected backup
                self._selected_backup = item.data(0, Qt.UserRole)
                self.restore_btn.setEnabled(True)
            else:
                # No item selected
                self._selected_backup = None
                self.restore_btn.setEnabled(False)
        finally:
            # Reconnect the signal
            self.backup_tree.itemChanged.connect(self._on_tree_item_changed)
    
    def _on_progress(self, message: str):
        """Handle progress updates from worker."""
        self.progress_text.append(message)
        # Auto-scroll to bottom
        cursor = self.progress_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.progress_text.setTextCursor(cursor)
    
    def _on_backup_finished(self, success: bool, message: str):
        """Handle backup completion."""
        self.progress_bar.setVisible(False)
        self.backup_btn.setEnabled(True)
        self.restore_btn.setEnabled(bool(self._selected_backup))
        
        self.progress_text.append(f"\n{'✅' if success else '❌'} {message}")
        
        if success:
            QMessageBox.information(self, "Backup Complete", message)
            self._populate_backup_tree()  # Refresh backup list
        else:
            QMessageBox.warning(self, "Backup Failed", message)
        
        self._worker = None
    
    def _on_restore_finished(self, success: bool, message: str):
        """Handle restore completion."""
        self.progress_bar.setVisible(False)
        self.backup_btn.setEnabled(True)
        self.restore_btn.setEnabled(bool(self._selected_backup))
        
        self.progress_text.append(f"\n{'✅' if success else '❌'} {message}")
        
        if success:
            QMessageBox.information(self, "Restore Complete", message + "\n\nRestart EVE Online for changes to take effect.")
            self._populate_backup_tree()  # Refresh to show new safety backup
        else:
            QMessageBox.warning(self, "Restore Failed", message)
        
        self._worker = None