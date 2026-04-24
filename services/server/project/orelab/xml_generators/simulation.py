"""
Simulation XML generator.

Copies and updates simulation.xml with base currency settings.
"""

from lxml import etree
from pathlib import Path
from typing import Optional


class SimulationGenerator:
    """
    Generate simulation.xml configuration file.

    Copies the template simulation.xml and updates base currency settings.
    """

    def __init__(self, template_path: Optional[Path] = None):
        """
        Initialize Simulation generator.

        Args:
            template_path: Path to template simulation.xml file.
        """
        self.template_path = template_path
        self._config_tree = None

    def load_template(self) -> None:
        """Load template simulation.xml file."""
        if self.template_path and self.template_path.exists():
            parser = etree.XMLParser(remove_blank_text=True)
            self._config_tree = etree.parse(str(self.template_path), parser)
        else:
            raise FileNotFoundError(f"Simulation template not found: {self.template_path}")

    def set_base_currency(self, currency: str) -> None:
        """
        Set base currency in simulation configuration.

        Args:
            currency: Base currency code (e.g., EUR, USD)
        """
        if self._config_tree is None:
            self.load_template()

        root = self._config_tree.getroot()

        # Update BaseCurrency element in Market section
        base_currency_elem = root.find(".//BaseCurrency")
        if base_currency_elem is not None:
            base_currency_elem.text = currency

        # Update DomesticCcy element in CrossAssetModel section
        domestic_ccy_elem = root.find(".//DomesticCcy")
        if domestic_ccy_elem is not None:
            domestic_ccy_elem.text = currency

    def save_to_file(self, output_path: Path) -> None:
        """
        Save configuration to file.

        Args:
            output_path: Path to output file
        """
        if self._config_tree is None:
            self.load_template()

        self._config_tree.write(
            str(output_path),
            encoding='utf-8',
            xml_declaration=True,
            pretty_print=True
        )
