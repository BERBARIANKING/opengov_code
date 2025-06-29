#!/usr/bin/env python3
"""
Government Data Portal Interoperability Analysis
Analyzes metadata-level interoperability across European government data portals
"""

import requests
import json
import time
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict, Counter
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class InteroperabilityMetrics:
    """Data class to store interoperability analysis results"""
    country: str
    total_datasets: int = 0
    
    # Metadata Standards
    dcat_compliance_score: float = 0.0
    dublin_core_compliance_score: float = 0.0
    metadata_completeness_score: float = 0.0
    
    # Machine-Readable Licensing
    cc_licenses: int = 0
    odbl_licenses: int = 0
    automated_license_detection_score: float = 0.0
    license_variety: List[str] = field(default_factory=list)
    
    # Controlled Vocabularies
    standardized_terminology_score: float = 0.0
    taxonomy_usage: Dict[str, int] = field(default_factory=dict)
    
    # Multilingual Support
    multilingual_support_score: float = 0.0
    supported_languages: List[str] = field(default_factory=list)
    
    # Persistent Identifiers
    doi_count: int = 0
    urn_count: int = 0
    uuid_count: int = 0
    handle_count: int = 0
    persistent_id_score: float = 0.0
    
    # API Response Quality
    api_response_time: float = 0.0
    api_success_rate: float = 0.0

class GovernmentDataAnalyzer:
    """Main analyzer class for government data portals"""
    
    def __init__(self):
        self.portals = {
            "Germany": "https://www.govdata.de/ckan/api/3/action/package_search",
            "Italy": "https://www.dati.gov.it/opendata/api/3/action/package_list",
            "Spain": "https://datos.gob.es/apidata/catalog/dataset",
            "Netherlands": "https://ckan.dataplatform.nl/api/3/action/package_search",
            "France": "https://www.data.gouv.fr/api/1/datasets/"
        }
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'GovernmentDataAnalyzer/1.0 (Research Purpose)'
        })
        
        # Standard vocabularies and patterns
        self.dcat_fields = [
            'dcat:Dataset', 'dcat:distribution', 'dcat:keyword', 'dcat:theme',
            'dcat:contactPoint', 'dcat:publisher', 'dcat:temporal', 'dcat:spatial'
        ]
        
        self.dublin_core_fields = [
            'dc:title', 'dc:creator', 'dc:subject', 'dc:description', 'dc:publisher',
            'dc:contributor', 'dc:date', 'dc:type', 'dc:format', 'dc:identifier',
            'dc:source', 'dc:language', 'dc:relation', 'dc:coverage', 'dc:rights'
        ]
        
        self.cc_licenses = [
            'cc-by', 'cc-by-sa', 'cc-by-nc', 'cc-by-nd', 'cc-by-nc-sa', 'cc-by-nc-nd',
            'cc0', 'creative-commons'
        ]
        
        self.persistent_id_patterns = {
            'doi': re.compile(r'10\.\d+/[^\s]+', re.IGNORECASE),
            'urn': re.compile(r'urn:[a-z0-9][a-z0-9-]{0,31}:[a-z0-9()+,\-.:=@;$_!*\'%/?#]+', re.IGNORECASE),
            'uuid': re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', re.IGNORECASE),
            'handle': re.compile(r'hdl\.handle\.net/[0-9.]+/[^\s]+', re.IGNORECASE)
        }

    def fetch_data_with_retry(self, url: str, params: Dict = None, max_retries: int = 3) -> Optional[Dict]:
        """Fetch data from API with retry logic"""
        for attempt in range(max_retries):
            try:
                start_time = time.time()
                response = self.session.get(url, params=params, timeout=30)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    return {
                        'data': response.json(),
                        'response_time': response_time,
                        'success': True
                    }
                else:
                    logger.warning(f"HTTP {response.status_code} for {url}")
                    
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed for {url}: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    
        return {'data': None, 'response_time': 0, 'success': False}

    def analyze_metadata_standards(self, dataset: Dict) -> Dict[str, float]:
        """Analyze DCAT and Dublin Core compliance"""
        dataset_str = json.dumps(dataset, default=str).lower()
        
        # DCAT compliance
        dcat_matches = sum(1 for field in self.dcat_fields if field.lower() in dataset_str)
        dcat_score = dcat_matches / len(self.dcat_fields) * 100
        
        # Dublin Core compliance
        dc_matches = sum(1 for field in self.dublin_core_fields if field.lower() in dataset_str)
        dc_score = dc_matches / len(self.dublin_core_fields) * 100
        
        # Metadata completeness (essential fields)
        essential_fields = ['title', 'description', 'license', 'publisher', 'modified']
        completeness = sum(1 for field in essential_fields if any(field in str(v).lower() for v in dataset.values() if v))
        completeness_score = completeness / len(essential_fields) * 100
        
        return {
            'dcat_score': dcat_score,
            'dublin_core_score': dc_score,
            'completeness_score': completeness_score
        }

    def analyze_licensing(self, dataset: Dict) -> Dict[str, Any]:
        """Analyze machine-readable licensing"""
        dataset_str = json.dumps(dataset, default=str).lower()
        
        cc_count = sum(1 for license_type in self.cc_licenses if license_type in dataset_str)
        odbl_count = 1 if 'odbl' in dataset_str or 'open database license' in dataset_str else 0
        
        # Extract license information
        license_info = []
        for key, value in dataset.items():
            if 'license' in str(key).lower() and value:
                license_info.append(str(value).lower())
        
        # Automated license detection score
        has_structured_license = any('license' in str(k).lower() for k in dataset.keys())
        has_license_url = any('license' in str(k).lower() and ('http' in str(v) or 'url' in str(v)) 
                            for k, v in dataset.items() if v)
        
        automation_score = (has_structured_license * 50) + (has_license_url * 50)
        
        return {
            'cc_licenses': cc_count,
            'odbl_licenses': odbl_count,
            'automation_score': automation_score,
            'license_variety': license_info
        }

    def analyze_vocabularies(self, dataset: Dict) -> Dict[str, Any]:
        """Analyze controlled vocabularies usage"""
        # Common government data themes/categories
        standard_themes = [
            'economy', 'education', 'environment', 'government', 'health',
            'society', 'transport', 'science', 'agriculture', 'energy'
        ]
        
        dataset_str = json.dumps(dataset, default=str).lower()
        theme_matches = {}
        
        for theme in standard_themes:
            if theme in dataset_str:
                theme_matches[theme] = theme_matches.get(theme, 0) + 1
        
        # Calculate standardization score based on theme usage
        standardization_score = min(len(theme_matches) / len(standard_themes) * 100, 100)
        
        return {
            'standardization_score': standardization_score,
            'theme_matches': theme_matches
        }

    def analyze_multilingual_support(self, dataset: Dict) -> Dict[str, Any]:
        """Analyze multilingual support"""
        # Language indicators
        language_indicators = ['en', 'de', 'fr', 'es', 'it', 'nl', 'language', 'lang']
        dataset_str = json.dumps(dataset, default=str).lower()
        
        detected_languages = []
        for indicator in language_indicators:
            if indicator in dataset_str:
                detected_languages.append(indicator)
        
        # Check for multilingual fields (multiple language versions)
        multilingual_fields = 0
        for key, value in dataset.items():
            if isinstance(value, dict) and any(lang in str(value).lower() for lang in ['en', 'de', 'fr', 'es', 'it', 'nl']):
                multilingual_fields += 1
        
        multilingual_score = min(multilingual_fields * 20, 100)  # Max 5 multilingual fields for 100%
        
        return {
            'multilingual_score': multilingual_score,
            'detected_languages': list(set(detected_languages))
        }

    def analyze_persistent_identifiers(self, dataset: Dict) -> Dict[str, int]:
        """Analyze persistent identifiers usage"""
        dataset_str = json.dumps(dataset, default=str)
        
        identifier_counts = {}
        for id_type, pattern in self.persistent_id_patterns.items():
            matches = pattern.findall(dataset_str)
            identifier_counts[id_type] = len(matches)
        
        # Calculate overall persistent ID score
        total_persistent_ids = sum(identifier_counts.values())
        persistence_score = min(total_persistent_ids * 25, 100)  # Max 4 different types for 100%
        
        return {
            **identifier_counts,
            'persistence_score': persistence_score
        }

    def analyze_country_portal(self, country: str, url: str, sample_size: int = 100) -> InteroperabilityMetrics:
        """Analyze a single country's data portal"""
        logger.info(f"Analyzing {country} portal...")
        
        metrics = InteroperabilityMetrics(country=country)
        
        # Fetch data based on portal type
        if 'ckan' in url or 'package_search' in url:
            params = {'rows': sample_size, 'start': 0}
            result = self.fetch_data_with_retry(url, params)
        elif 'package_list' in url:
            result = self.fetch_data_with_retry(url)
        elif country == 'France':
            params = {'page_size': sample_size}
            result = self.fetch_data_with_retry(url, params)
        else:
            params = {'limit': sample_size}
            result = self.fetch_data_with_retry(url, params)
        
        if not result['success'] or not result['data']:
            logger.error(f"Failed to fetch data from {country}")
            return metrics
        
        metrics.api_response_time = result['response_time']
        metrics.api_success_rate = 100.0
        
        # Extract datasets from response
        datasets = self.extract_datasets(result['data'], country)
        metrics.total_datasets = len(datasets)
        
        if not datasets:
            logger.warning(f"No datasets found for {country}")
            return metrics
        
        # Analyze each dataset
        all_metadata_scores = []
        all_license_data = []
        all_vocabulary_data = []
        all_multilingual_data = []
        all_persistent_id_data = []
        
        for dataset in datasets[:sample_size]:  # Limit analysis to sample size
            # Metadata standards
            metadata_analysis = self.analyze_metadata_standards(dataset)
            all_metadata_scores.append(metadata_analysis)
            
            # Licensing
            license_analysis = self.analyze_licensing(dataset)
            all_license_data.append(license_analysis)
            
            # Vocabularies
            vocab_analysis = self.analyze_vocabularies(dataset)
            all_vocabulary_data.append(vocab_analysis)
            
            # Multilingual support
            multilingual_analysis = self.analyze_multilingual_support(dataset)
            all_multilingual_data.append(multilingual_analysis)
            
            # Persistent identifiers
            persistent_id_analysis = self.analyze_persistent_identifiers(dataset)
            all_persistent_id_data.append(persistent_id_analysis)
        
        # Aggregate results
        self.aggregate_metrics(metrics, all_metadata_scores, all_license_data, 
                             all_vocabulary_data, all_multilingual_data, all_persistent_id_data)
        
        return metrics

    def extract_datasets(self, data: Dict, country: str) -> List[Dict]:
        """Extract datasets from API response based on country-specific format"""
        datasets = []
        
        try:
            if country in ['Germany', 'Netherlands']:
                # CKAN format
                if 'result' in data and 'results' in data['result']:
                    datasets = data['result']['results']
            elif country == 'Italy':
                # Package list format - need to fetch individual packages
                if 'result' in data:
                    datasets = data['result'][:50]  # Limit for analysis
            elif country == 'France':
                # Data.gouv.fr format
                if 'data' in data:
                    datasets = data['data']
            elif country == 'Spain':
                # Spanish portal format
                if isinstance(data, list):
                    datasets = data
                elif 'result' in data:
                    datasets = data['result']
                    
        except Exception as e:
            logger.error(f"Error extracting datasets for {country}: {str(e)}")
            
        return datasets

    def aggregate_metrics(self, metrics: InteroperabilityMetrics, metadata_scores: List[Dict],
                         license_data: List[Dict], vocabulary_data: List[Dict],
                         multilingual_data: List[Dict], persistent_id_data: List[Dict]):
        """Aggregate analysis results into metrics"""
        
        if not metadata_scores:
            return
            
        # Metadata standards
        metrics.dcat_compliance_score = sum(s['dcat_score'] for s in metadata_scores) / len(metadata_scores)
        metrics.dublin_core_compliance_score = sum(s['dublin_core_score'] for s in metadata_scores) / len(metadata_scores)
        metrics.metadata_completeness_score = sum(s['completeness_score'] for s in metadata_scores) / len(metadata_scores)
        
        # Licensing
        metrics.cc_licenses = sum(l['cc_licenses'] for l in license_data)
        metrics.odbl_licenses = sum(l['odbl_licenses'] for l in license_data)
        metrics.automated_license_detection_score = sum(l['automation_score'] for l in license_data) / len(license_data)
        all_licenses = [license for l in license_data for license in l['license_variety']]
        metrics.license_variety = list(set(all_licenses))
        
        # Vocabularies
        metrics.standardized_terminology_score = sum(v['standardization_score'] for v in vocabulary_data) / len(vocabulary_data)
        all_themes = defaultdict(int)
        for v in vocabulary_data:
            for theme, count in v['theme_matches'].items():
                all_themes[theme] += count
        metrics.taxonomy_usage = dict(all_themes)
        
        # Multilingual support
        metrics.multilingual_support_score = sum(m['multilingual_score'] for m in multilingual_data) / len(multilingual_data)
        all_languages = [lang for m in multilingual_data for lang in m['detected_languages']]
        metrics.supported_languages = list(set(all_languages))
        
        # Persistent identifiers
        metrics.doi_count = sum(p['doi'] for p in persistent_id_data)
        metrics.urn_count = sum(p['urn'] for p in persistent_id_data)
        metrics.uuid_count = sum(p['uuid'] for p in persistent_id_data)
        metrics.handle_count = sum(p['handle'] for p in persistent_id_data)
        metrics.persistent_id_score = sum(p['persistence_score'] for p in persistent_id_data) / len(persistent_id_data)

    def generate_report(self, all_metrics: List[InteroperabilityMetrics]) -> str:
        """Generate comprehensive analysis report"""
        report = []
        report.append("="*80)
        report.append("GOVERNMENT DATA PORTAL INTEROPERABILITY ANALYSIS REPORT")
        report.append("="*80)
        report.append(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Countries Analyzed: {len(all_metrics)}")
        report.append("")
        
        # Executive Summary
        report.append("EXECUTIVE SUMMARY")
        report.append("-" * 50)
        
        avg_dcat = sum(m.dcat_compliance_score for m in all_metrics) / len(all_metrics)
        avg_dc = sum(m.dublin_core_compliance_score for m in all_metrics) / len(all_metrics)
        avg_license = sum(m.automated_license_detection_score for m in all_metrics) / len(all_metrics)
        avg_multilingual = sum(m.multilingual_support_score for m in all_metrics) / len(all_metrics)
        avg_persistent = sum(m.persistent_id_score for m in all_metrics) / len(all_metrics)
        
        report.append(f"Average DCAT Compliance: {avg_dcat:.1f}%")
        report.append(f"Average Dublin Core Compliance: {avg_dc:.1f}%")
        report.append(f"Average License Automation: {avg_license:.1f}%")
        report.append(f"Average Multilingual Support: {avg_multilingual:.1f}%")
        report.append(f"Average Persistent ID Usage: {avg_persistent:.1f}%")
        report.append("")
        
        # Country-by-Country Analysis
        for metrics in sorted(all_metrics, key=lambda x: x.dcat_compliance_score, reverse=True):
            report.append(f"COUNTRY: {metrics.country}")
            report.append("-" * 30)
            
            report.append(f"Total Datasets Analyzed: {metrics.total_datasets}")
            report.append(f"API Response Time: {metrics.api_response_time:.2f}s")
            report.append("")
            
            report.append("Metadata Standards:")
            report.append(f"  DCAT Compliance: {metrics.dcat_compliance_score:.1f}%")
            report.append(f"  Dublin Core Compliance: {metrics.dublin_core_compliance_score:.1f}%")
            report.append(f"  Metadata Completeness: {metrics.metadata_completeness_score:.1f}%")
            report.append("")
            
            report.append("Machine-Readable Licensing:")
            report.append(f"  Creative Commons Licenses: {metrics.cc_licenses}")
            report.append(f"  ODbL Licenses: {metrics.odbl_licenses}")
            report.append(f"  Automated Detection Score: {metrics.automated_license_detection_score:.1f}%")
            report.append(f"  License Variety: {len(metrics.license_variety)} unique types")
            report.append("")
            
            report.append("Controlled Vocabularies:")
            report.append(f"  Standardized Terminology Score: {metrics.standardized_terminology_score:.1f}%")
            report.append(f"  Top Themes: {', '.join(list(metrics.taxonomy_usage.keys())[:5])}")
            report.append("")
            
            report.append("Multilingual Support:")
            report.append(f"  Multilingual Support Score: {metrics.multilingual_support_score:.1f}%")
            report.append(f"  Supported Languages: {', '.join(metrics.supported_languages)}")
            report.append("")
            
            report.append("Persistent Identifiers:")
            report.append(f"  DOI Count: {metrics.doi_count}")
            report.append(f"  URN Count: {metrics.urn_count}")
            report.append(f"  UUID Count: {metrics.uuid_count}")
            report.append(f"  Handle Count: {metrics.handle_count}")
            report.append(f"  Overall Persistence Score: {metrics.persistent_id_score:.1f}%")
            report.append("")
            report.append("-" * 50)
            report.append("")
        
        # Recommendations
        report.append("RECOMMENDATIONS")
        report.append("-" * 50)
        
        best_dcat = max(all_metrics, key=lambda x: x.dcat_compliance_score)
        worst_dcat = min(all_metrics, key=lambda x: x.dcat_compliance_score)
        
        report.append(f"1. DCAT Compliance: {best_dcat.country} leads with {best_dcat.dcat_compliance_score:.1f}%")
        report.append(f"   {worst_dcat.country} should improve from {worst_dcat.dcat_compliance_score:.1f}%")
        report.append("")
        
        best_multilingual = max(all_metrics, key=lambda x: x.multilingual_support_score)
        report.append(f"2. Multilingual Support: {best_multilingual.country} excels with {best_multilingual.multilingual_support_score:.1f}%")
        report.append("   Other countries should enhance i18n support")
        report.append("")
        
        best_licensing = max(all_metrics, key=lambda x: x.automated_license_detection_score)
        report.append(f"3. License Automation: {best_licensing.country} shows best practices at {best_licensing.automated_license_detection_score:.1f}%")
        report.append("   Structured, machine-readable licensing should be prioritized")
        report.append("")
        
        return "\n".join(report)

    def run_analysis(self, sample_size: int = 50) -> str:
        """Run complete analysis on all portals"""
        logger.info("Starting government data portal analysis...")
        
        all_metrics = []
        
        for country, url in self.portals.items():
            try:
                metrics = self.analyze_country_portal(country, url, sample_size)
                all_metrics.append(metrics)
                logger.info(f"Completed analysis for {country}")
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Failed to analyze {country}: {str(e)}")
                continue
        
        if not all_metrics:
            return "No data could be analyzed from any portal."
        
        # Generate and return report
        report = self.generate_report(all_metrics)
        
        # Also save raw metrics as JSON
        metrics_data = []
        for m in all_metrics:
            metrics_dict = {
                'country': m.country,
                'total_datasets': m.total_datasets,
                'dcat_compliance_score': m.dcat_compliance_score,
                'dublin_core_compliance_score': m.dublin_core_compliance_score,
                'metadata_completeness_score': m.metadata_completeness_score,
                'cc_licenses': m.cc_licenses,
                'odbl_licenses': m.odbl_licenses,
                'automated_license_detection_score': m.automated_license_detection_score,
                'license_variety_count': len(m.license_variety),
                'standardized_terminology_score': m.standardized_terminology_score,
                'multilingual_support_score': m.multilingual_support_score,
                'supported_languages_count': len(m.supported_languages),
                'persistent_id_score': m.persistent_id_score,
                'api_response_time': m.api_response_time
            }
            metrics_data.append(metrics_dict)
        
        # Save JSON report
        with open(f'government_data_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json', 'w') as f:
            json.dump(metrics_data, f, indent=2)
        
        return report

def main():
    """Main execution function"""
    analyzer = GovernmentDataAnalyzer()
    
    print("Government Data Portal Interoperability Analysis")
    print("=" * 60)
    print("This analysis will evaluate European government data portals for:")
    print("• Metadata standards compliance (DCAT, Dublin Core)")
    print("• Machine-readable licensing")
    print("• Controlled vocabularies usage")
    print("• Multilingual support")
    print("• Persistent identifiers")
    print()
    
    sample_size = input("Enter sample size per country (default 50): ") or "50"
    
    try:
        sample_size = int(sample_size)
        if sample_size < 1 or sample_size > 500:
            raise ValueError("Sample size must be between 1 and 500")
    except ValueError as e:
        print(f"Invalid sample size: {e}")
        sample_size = 50
    
    print(f"\nStarting analysis with sample size: {sample_size}")
    print("This may take several minutes...\n")
    
    # Run analysis
    report = analyzer.run_analysis(sample_size)
    
    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'government_data_report_{timestamp}.txt'
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(report)
    print(f"\nFull report saved to: {filename}")
    print(f"JSON data saved to: government_data_analysis_{timestamp}.json")

if __name__ == "__main__":
    main()
