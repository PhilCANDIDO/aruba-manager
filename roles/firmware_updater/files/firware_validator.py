#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Firmware Validator for Aruba AOS-CX

Ce script valide les fichiers firmware Aruba AOS-CX avant upload.
Il vérifie l'intégrité, la compatibilité et la taille des fichiers.

Usage:
    python firmware_validator.py firmware_file.swi

Auteur: Aruba Manager Team
"""

import os
import sys
import hashlib
import argparse
import logging
import re
from pathlib import Path

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ArubaFirmwareValidator:
    """Validateur pour les fichiers firmware Aruba AOS-CX."""
    
    def __init__(self, firmware_path):
        """
        Initialiser le validateur.
        
        Args:
            firmware_path (str): Chemin vers le fichier firmware
        """
        self.firmware_path = Path(firmware_path)
        self.validation_results = {}
        
        # Patterns de validation
        self.version_pattern = r'^[A-Z]{2}\.\d{2}\.\d{2}\.\d{4}$'
        self.filename_pattern = r'^ArubaOS-CX_.+\.swi$'
        
        # Tailles minimales/maximales attendues (en MB)
        self.min_size_mb = 400
        self.max_size_mb = 2000
        
        # Modèles supportés et leurs contraintes
        self.supported_models = {
            '6100': {'min_size': 400, 'max_size': 800},
            '6200': {'min_size': 450, 'max_size': 900},
            '6300': {'min_size': 500, 'max_size': 1000},
            '6400': {'min_size': 600, 'max_size': 1200},
            '8320': {'min_size': 700, 'max_size': 1500},
            '8325': {'min_size': 700, 'max_size': 1500},
            '8400': {'min_size': 800, 'max_size': 2000},
        }
    
    def validate_file_exists(self):
        """Vérifier que le fichier existe et est accessible."""
        try:
            if not self.firmware_path.exists():
                self.validation_results['file_exists'] = {
                    'status': False,
                    'error': f"Fichier non trouvé: {self.firmware_path}"
                }
                return False
            
            if not self.firmware_path.is_file():
                self.validation_results['file_exists'] = {
                    'status': False,
                    'error': f"Le chemin n'est pas un fichier: {self.firmware_path}"
                }
                return False
            
            self.validation_results['file_exists'] = {
                'status': True,
                'path': str(self.firmware_path),
                'size_bytes': self.firmware_path.stat().st_size
            }
            return True
            
        except Exception as e:
            self.validation_results['file_exists'] = {
                'status': False,
                'error': f"Erreur d'accès au fichier: {str(e)}"
            }
            return False
    
    def validate_filename(self):
        """Valider le nom du fichier."""
        filename = self.firmware_path.name
        
        if re.match(self.filename_pattern, filename):
            self.validation_results['filename'] = {
                'status': True,
                'filename': filename
            }
            return True
        else:
            self.validation_results['filename'] = {
                'status': False,
                'error': f"Nom de fichier invalide: {filename}. Attendu: ArubaOS-CX_*.swi"
            }
            return False
    
    def validate_file_size(self):
        """Valider la taille du fichier."""
        try:
            size_bytes = self.firmware_path.stat().st_size
            size_mb = size_bytes / (1024 * 1024)
            
            if size_mb < self.min_size_mb:
                self.validation_results['file_size'] = {
                    'status': False,
                    'error': f"Fichier trop petit: {size_mb:.1f}MB (minimum: {self.min_size_mb}MB)"
                }
                return False
            
            if size_mb > self.max_size_mb:
                self.validation_results['file_size'] = {
                    'status': False,
                    'error': f"Fichier trop gros: {size_mb:.1f}MB (maximum: {self.max_size_mb}MB)"
                }
                return False
            
            self.validation_results['file_size'] = {
                'status': True,
                'size_mb': round(size_mb, 1),
                'size_bytes': size_bytes
            }
            return True
            
        except Exception as e:
            self.validation_results['file_size'] = {
                'status': False,
                'error': f"Erreur lors de la vérification de taille: {str(e)}"
            }
            return False
    
    def calculate_checksum(self, algorithm='sha256'):
        """Calculer le checksum du fichier."""
        try:
            hash_func = hashlib.new(algorithm)
            
            with open(self.firmware_path, 'rb') as f:
                # Lire par chunks pour économiser la mémoire
                for chunk in iter(lambda: f.read(8192), b""):
                    hash_func.update(chunk)
            
            checksum = hash_func.hexdigest()
            
            self.validation_results['checksum'] = {
                'status': True,
                'algorithm': algorithm,
                'checksum': checksum
            }
            return checksum
            
        except Exception as e:
            self.validation_results['checksum'] = {
                'status': False,
                'error': f"Erreur lors du calcul de checksum: {str(e)}"
            }
            return None
    
    def extract_version_from_filename(self):
        """Extraire la version du firmware depuis le nom de fichier."""
        filename = self.firmware_path.name
        
        # Patterns communs pour extraire la version
        patterns = [
            r'ArubaOS-CX_\w+_(\d+)_(\d+)_(\d+)\.swi',  # Format: XX_YY_ZZZZ
            r'([A-Z]{2})\.(\d{2})\.(\d{2})\.(\d{4})',   # Format: LL.XX.YY.ZZZZ
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename)
            if match:
                if len(match.groups()) == 3:
                    # Format XX_YY_ZZZZ
                    version = f"LL.{match.group(1)}.{match.group(2)}.{match.group(3)}"
                elif len(match.groups()) == 4:
                    # Format LL.XX.YY.ZZZZ
                    version = f"{match.group(1)}.{match.group(2)}.{match.group(3)}.{match.group(4)}"
                else:
                    continue
                
                self.validation_results['version_extraction'] = {
                    'status': True,
                    'version': version,
                    'pattern_used': pattern
                }
                return version
        
        self.validation_results['version_extraction'] = {
            'status': False,
            'error': "Impossible d'extraire la version du nom de fichier"
        }
        return None
    
    def validate_model_compatibility(self, target_model=None):
        """Valider la compatibilité avec un modèle spécifique."""
        if not target_model:
            # Essayer d'extraire le modèle du nom de fichier
            filename = self.firmware_path.name
            for model in self.supported_models.keys():
                if model in filename:
                    target_model = model
                    break
        
        if not target_model:
            self.validation_results['model_compatibility'] = {
                'status': True,
                'message': "Aucun modèle spécifique détecté, validation générique appliquée"
            }
            return True
        
        if target_model not in self.supported_models:
            self.validation_results['model_compatibility'] = {
                'status': False,
                'error': f"Modèle non supporté: {target_model}"
            }
            return False
        
        # Vérifier les contraintes spécifiques au modèle
        model_constraints = self.supported_models[target_model]
        size_mb = self.validation_results.get('file_size', {}).get('size_mb', 0)
        
        if size_mb < model_constraints['min_size']:
            self.validation_results['model_compatibility'] = {
                'status': False,
                'error': f"Fichier trop petit pour {target_model}: {size_mb}MB (min: {model_constraints['min_size']}MB)"
            }
            return False
        
        if size_mb > model_constraints['max_size']:
            self.validation_results['model_compatibility'] = {
                'status': False,
                'error': f"Fichier trop gros pour {target_model}: {size_mb}MB (max: {model_constraints['max_size']}MB)"
            }
            return False
        
        self.validation_results['model_compatibility'] = {
            'status': True,
            'target_model': target_model,
            'constraints_met': True
        }
        return True
    
    def run_full_validation(self, target_model=None):
        """Exécuter toutes les validations."""
        logger.info(f"Début de la validation de {self.firmware_path}")
        
        validations = [
            ('file_exists', self.validate_file_exists),
            ('filename', self.validate_filename),
            ('file_size', self.validate_file_size),
            ('checksum', lambda: self.calculate_checksum()),
            ('version_extraction', self.extract_version_from_filename),
            ('model_compatibility', lambda: self.validate_model_compatibility(target_model)),
        ]
        
        all_passed = True
        for validation_name, validation_func in validations:
            try:
                result = validation_func()
                if not result:
                    all_passed = False
                    logger.error(f"Validation {validation_name} échouée")
                else:
                    logger.info(f"Validation {validation_name} réussie")
            except Exception as e:
                logger.error(f"Erreur durant la validation {validation_name}: {str(e)}")
                all_passed = False
        
        # Résumé final
        self.validation_results['overall'] = {
            'status': all_passed,
            'total_validations': len(validations),
            'passed_validations': sum(1 for v in self.validation_results.values() 
                                    if isinstance(v, dict) and v.get('status', False)),
            'timestamp': __import__('datetime').datetime.now().isoformat()
        }
        
        return all_passed
    
    def get_validation_report(self):
        """Générer un rapport de validation détaillé."""
        report = {
            'firmware_file': str(self.firmware_path),
            'validation_results': self.validation_results,
            'summary': self.validation_results.get('overall', {})
        }
        return report
    
    def print_validation_summary(self):
        """Afficher un résumé de la validation."""
        print("\n" + "="*60)
        print("RÉSUMÉ DE LA VALIDATION FIRMWARE")
        print("="*60)
        print(f"Fichier: {self.firmware_path.name}")
        
        if 'file_size' in self.validation_results:
            size_info = self.validation_results['file_size']
            if size_info['status']:
                print(f"Taille: {size_info['size_mb']}MB")
        
        if 'version_extraction' in self.validation_results:
            version_info = self.validation_results['version_extraction']
            if version_info['status']:
                print(f"Version détectée: {version_info['version']}")
        
        if 'checksum' in self.validation_results:
            checksum_info = self.validation_results['checksum']
            if checksum_info['status']:
                print(f"Checksum SHA256: {checksum_info['checksum'][:16]}...")
        
        print("\nRésultats des validations:")
        for key, result in self.validation_results.items():
            if key == 'overall':
                continue
            
            if isinstance(result, dict):
                status = "✓" if result.get('status', False) else "✗"
                print(f"  {status} {key.replace('_', ' ').title()}")
                if not result.get('status', False) and 'error' in result:
                    print(f"    Erreur: {result['error']}")
        
        overall = self.validation_results.get('overall', {})
        print(f"\nStatut global: {'✓ VALIDÉ' if overall.get('status', False) else '✗ ÉCHEC'}")
        print(f"Validations réussies: {overall.get('passed_validations', 0)}/{overall.get('total_validations', 0)}")
        print("="*60)


def main():
    """Point d'entrée principal du script."""
    parser = argparse.ArgumentParser(
        description="Valider un fichier firmware Aruba AOS-CX",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:
  python firmware_validator.py firmware.swi
  python firmware_validator.py --model 6200 firmware.swi
  python firmware_validator.py --quiet --json firmware.swi
        """
    )
    
    parser.add_argument(
        'firmware_file',
        help='Chemin vers le fichier firmware (.swi)'
    )
    
    parser.add_argument(
        '--model',
        help='Modèle de switch cible pour validation spécifique',
        choices=['6100', '6200', '6300', '6400', '8320', '8325', '8400']
    )
    
    parser.add_argument(
        '--json',
        action='store_true',
        help='Sortie au format JSON'
    )
    
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Mode silencieux (erreurs uniquement)'
    )
    
    parser.add_argument(
        '--checksum-only',
        action='store_true',
        help='Calculer uniquement le checksum'
    )
    
    args = parser.parse_args()
    
    # Configuration du logging selon les options
    if args.quiet:
        logging.getLogger().setLevel(logging.ERROR)
    
    # Validation du fichier
    validator = ArubaFirmwareValidator(args.firmware_file)
    
    if args.checksum_only:
        # Mode checksum uniquement
        if validator.validate_file_exists():
            checksum = validator.calculate_checksum()
            if checksum:
                if args.json:
                    import json
                    print(json.dumps({
                        'file': args.firmware_file,
                        'checksum': checksum,
                        'algorithm': 'sha256'
                    }, indent=2))
                else:
                    print(f"SHA256: {checksum}")
                sys.exit(0)
            else:
                print("Erreur lors du calcul du checksum", file=sys.stderr)
                sys.exit(1)
        else:
            print("Fichier inaccessible", file=sys.stderr)
            sys.exit(1)
    
    # Validation complète
    success = validator.run_full_validation(args.model)
    
    if args.json:
        # Sortie JSON
        import json
        report = validator.get_validation_report()
        print(json.dumps(report, indent=2))
    else:
        # Sortie texte
        validator.print_validation_summary()
    
    # Code de sortie
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()