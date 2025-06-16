# readme_generation/readme_generator.py

import os
import sys
import yaml
import re
import logging
from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class GeneratorConfig:
    template_file: str
    output_file: str
    data_directory: str
    sections: List[Dict[str, Any]]
    validation: Dict[str, Any]
    logging_config: Dict[str, Any]


class ReadmeGenerator:
    def __init__(self, config_file: str = "config.yaml"):
        self.config = self._load_config(config_file)
        self._setup_logging()
        self.variables = {}
        self.missing_placeholders = set()
        self.unused_variables = set()
        
    def _load_config(self, config_file: str) -> GeneratorConfig:
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            return GeneratorConfig(
                template_file=config_data['generator']['template_file'],
                output_file=config_data['generator']['output_file'],
                data_directory=config_data['generator'].get('data_directory', '.'),
                sections=config_data['sections'],
                validation=config_data.get('validation', {}),
                logging_config=config_data.get('logging', {})
            )
        except FileNotFoundError:
            print(f"Config file '{config_file}' not found. Creating default config...")
            self._create_default_config(config_file)
            sys.exit(1)
        except yaml.YAMLError as e:
            print(f"Error parsing config file: {e}")
            sys.exit(1)
    
    def _create_default_config(self, config_file: str):
        default_config = {
            'generator': {
                'template_file': 'README.template',
                'output_file': 'README.md',
                'data_directory': '.'
            },
            'sections': [
                {'name': 'title', 'file': 'title.yaml', 'required': True}
            ],
            'validation': {
                'check_placeholders': True,
                'strict_mode': False
            },
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(levelname)s - %(message)s'
            }
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(default_config, f, default_flow_style=False, indent=2)
        
        print(f"Created default config file: {config_file}")
    
    def _setup_logging(self):
        log_level = getattr(logging, self.config.logging_config.get('level', 'INFO'))
        log_format = self.config.logging_config.get('format', '%(asctime)s - %(levelname)s - %(message)s')
        
        logging.basicConfig(level=log_level, format=log_format)
        self.logger = logging.getLogger(__name__)
    
    def load_data_files(self) -> Dict[str, Any]:
        self.logger.info("Loading YAML data files...")
        variables = {}
        
        for section in self.config.sections:
            file_path = os.path.join(self.config.data_directory, section['file'])
            
            try:
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        section_data = yaml.safe_load(f)
                    
                    if section_data:
                        variables.update(section_data)
                        self.logger.debug(f"Loaded {section['name']}: {section['file']}")
                    else:
                        self.logger.warning(f"Empty file: {section['file']}")
                
                elif section['required']:
                    self.logger.error(f"Required file missing: {section['file']}")
                    raise FileNotFoundError(f"Required section file not found: {file_path}")
                else:
                    self.logger.info(f"ℹOptional file not found: {section['file']}")
                    
            except yaml.YAMLError as e:
                self.logger.error(f"Error parsing {section['file']}: {e}")
                if section['required']:
                    raise
            except Exception as e:
                self.logger.error(f"Unexpected error loading {section['file']}: {e}")
                if section['required']:
                    raise
        
        self.variables = variables
        self.logger.info(f"Loaded {len(variables)} variables from {len(self.config.sections)} sections")
        return variables
    
    def load_template(self) -> str:
        template_path = self.config.template_file
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            self.logger.info(f"Loaded template: {template_path}")
            return template_content
            
        except FileNotFoundError:
            self.logger.error(f"Template file not found: {template_path}")
            raise
        except Exception as e:
            self.logger.error(f"Error loading template: {e}")
            raise
    
    def find_placeholders(self, template: str) -> set:
        # Find all [placeholder] patterns
        placeholder_pattern = r'\[([^\]]+)\]'
        placeholders = set(re.findall(placeholder_pattern, template))
        
        self.logger.debug(f"Found {len(placeholders)} placeholders in template")
        return placeholders
    
    def validate_data(self, template: str) -> bool:
        if not self.config.validation.get('check_placeholders', True):
            return True
        
        placeholders = self.find_placeholders(template)
        available_vars = set(self.variables.keys())
        
        # Find missing placeholders
        self.missing_placeholders = placeholders - available_vars
        
        # Find unused variables
        self.unused_variables = available_vars - placeholders
        
        # Report issues
        if self.missing_placeholders:
            self.logger.warning(f"Missing data for placeholders: {sorted(self.missing_placeholders)}")
        
        if self.unused_variables:
            self.logger.info(f"ℹUnused variables: {sorted(self.unused_variables)}")
        
        # Check if validation should fail
        strict_mode = self.config.validation.get('strict_mode', False)
        if strict_mode and self.missing_placeholders:
            self.logger.error("Strict mode: Cannot proceed with missing placeholders")
            return False
        
        return True
    
    def process_template(self, template: str) -> str:
        self.logger.info("Processing template...")
        
        processed_template = template
        replaced_count = 0
        
        # Replace placeholders with values
        for key, value in self.variables.items():
            placeholder = f"[{key}]"
            if placeholder in processed_template:
                # Convert value to string, handling multiline text properly
                str_value = str(value) if value is not None else ""
                processed_template = processed_template.replace(placeholder, str_value)
                replaced_count += 1
                self.logger.debug(f"Replaced [{key}] with value")
        
        # Handle missing placeholders in non-strict mode
        if not self.config.validation.get('strict_mode', False):
            # Replace remaining placeholders with empty strings or warning messages
            for placeholder in self.missing_placeholders:
                pattern = f"[{placeholder}]"
                if pattern in processed_template:
                    replacement = f"<!-- MISSING: {placeholder} -->"
                    processed_template = processed_template.replace(pattern, replacement)
                    self.logger.debug(f"Replaced missing placeholder [{placeholder}] with comment")
        
        self.logger.info(f"Replaced {replaced_count} placeholders")
        return processed_template
    
    def write_output(self, content: str):
        output_path = self.config.output_file
        
        try:
            # Create directory if it doesn't exist
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.logger.info(f"README generated successfully: {output_path}")
            
        except Exception as e:
            self.logger.error(f"Error writing output file: {e}")
            raise
    
    def generate(self) -> bool:
        try:
            self.logger.info("Starting README generation...")
            
            # Load data and template
            self.load_data_files()
            template = self.load_template()
            
            # Validate data
            if not self.validate_data(template):
                return False
            
            # Process template
            processed_content = self.process_template(template)
            
            # Write output
            self.write_output(processed_content)
            
            # Summary
            self._print_summary()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Generation failed: {e}")
            return False
    
    def _print_summary(self):
        print("\n" + "="*50)
        print("README GENERATION SUMMARY")
        print("="*50)
        print(f"Output file: {self.config.output_file}")
        print(f"Variables processed: {len(self.variables)}")
        
        if self.missing_placeholders:
            print(f"Missing placeholders: {len(self.missing_placeholders)}")
            for placeholder in sorted(self.missing_placeholders):
                print(f"   - [{placeholder}]")
        
        if self.unused_variables:
            print(f"ℹUnused variables: {len(self.unused_variables)}")
        
        print("="*50)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate README.md from template and YAML data")
    parser.add_argument(
        "-c", "--config", 
        default="config.yaml",
        help="Configuration file path (default: config.yaml)"
    )
    parser.add_argument(
        "-v", "--verbose", 
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Override logging level if verbose
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        generator = ReadmeGenerator(args.config)
        success = generator.generate()
        
        if success:
            print("\nREADME.md generated successfully!")
            sys.exit(0)
        else:
            print("\nREADME generation failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⏹Generation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 