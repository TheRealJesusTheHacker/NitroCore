"""
Advanced Layout Manager utility for assembling responsive widget matrices.
Handles clean underlying object unwrapping for custom compound UI widgets.
"""

import tkinter as tk
from typing import List, Tuple, Union, Any


class LayoutManager:
    """
    High-performance layout manager engine built for NitroCore.
    Safely interfaces with custom high-end UI elements or native Tkinter components.
    """
    
    @staticmethod
    def _unwrap_element(element: Any) -> tk.Widget:
        """
        Internal safety helper to extract raw underlying Tkinter components.
        Enables seamless support for both standard widgets and custom UI classes.
        """
        # Checks if it's one of our wrapped classes (which store the raw widget in self.widget)
        if hasattr(element, 'widget') and isinstance(element.widget, tk.Widget):
            return element.widget
        elif isinstance(element, tk.Widget):
            return element
        else:
            raise TypeError(f"Unsupported layout element type passed to manager: {type(element)}")

    @classmethod
    def vertical_stack(cls, elements: List[Any], spacing: int = 5) -> None:
        """Stacks elements vertically, stretching them horizontally to match parent width."""
        for element in elements:
            raw_widget = cls._unwrap_element(element)
            raw_widget.pack(fill=tk.X, padx=10, pady=spacing)
    
    @classmethod
    def horizontal_stack(cls, elements: List[Any], spacing: int = 5) -> None:
        """Stacks elements horizontally in a tight row format."""
        for element in elements:
            raw_widget = cls._unwrap_element(element)
            raw_widget.pack(side=tk.LEFT, padx=spacing, pady=spacing)
    
    @classmethod
    def grid_layout(
        cls,
        elements: List[Any],
        cols: int,
        spacing: Tuple[int, int] = (5, 5),
        sticky: str = 'nsew' # Default to fill all four quadrant anchor limits
    ) -> None:
        """Arranges elements cleanly inside a uniform dimensional grid."""
        for i, element in enumerate(elements):
            raw_widget = cls._unwrap_element(element)
            row = i // cols
            col = i % cols
            
            # Configure parenting container metrics automatically to ensure grid spaces match
            parent = raw_widget.master
            parent.columnconfigure(col, weight=1)
            parent.rowconfigure(row, weight=1)
            
            raw_widget.grid(
                row=row,
                column=col,
                padx=spacing[0],
                pady=spacing[1],
                sticky=sticky
            )
    
    @classmethod
    def form_layout(cls, fields: List[Tuple[str, Any]], spacing: int = 10) -> None:
        """
        Builds sleek double-column standard configurations.
        Exposes left-aligned descriptive tags mirrored beside active entry elements.
        """
        # Import dynamically here to avoid circular dependencies during initialization
        from .label import CustomLabel
        
        for i, (label_text, control_element) in enumerate(fields):
            raw_control = cls._unwrap_element(control_element)
            parent = raw_control.master
            
            # Automatically assign column sizing weights to the master frame canvas
            parent.columnconfigure(1, weight=3) # Let entry input fields dominate empty space
            
            # Instantiate our custom dark-themed text components cleanly
            lbl = CustomLabel(
                parent=parent,
                text=label_text,
                font=("Segoe UI", 10, "bold"),
                fg="#B9BBBE",
                bg=parent.cget("bg"),
            )

            lbl.grid(row=i, column=0, sticky="w", padx=spacing, pady=spacing // 2)
            raw_control.grid(row=i, column=1, sticky='ew', padx=spacing, pady=spacing // 2)
