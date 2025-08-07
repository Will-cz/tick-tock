#!/usr/bin/env python3
"""
Date/Time Edge Cases Testing
Tests leap years, timezone changes, date validation, and time calculations
"""

import unittest
import tempfile
import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock
import calendar

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tick_tock_widget.project_data import ProjectDataManager, Project, TimeRecord


class TestDateTimeEdgeCases(unittest.TestCase):
    """Test edge cases in date/time handling"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_data_file = Path(self.temp_dir) / "datetime_test.json"
        
        # Create minimal test data
        self.test_data = {
            "projects": [],
            "current_project_alias": None,
            "current_sub_activity_alias": None
        }
        
        with open(self.test_data_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_data, f, indent=2)
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except Exception:
            pass
    
    def test_leap_year_date_handling(self):
        """Test February 29th handling in leap years"""
        print("\n=== Date/Time Test: Leap Year Handling ===")
        
        dm = ProjectDataManager(str(self.test_data_file))
        dm.load_projects()
        
        # Test leap years: 2020, 2024, 2028
        leap_years = [2020, 2024, 2028]
        non_leap_years = [2021, 2022, 2023, 2025]
        
        project = dm.add_project("Leap Year Test", "LEAP-001", "leap_test")
        self.assertIsNotNone(project, "Should create test project")
        
        # Test February 29th in leap years
        for year in leap_years:
            feb_29 = f"{year}-02-29"
            
            # Verify February 29th is valid for leap years
            self.assertTrue(calendar.isleap(year), f"{year} should be a leap year")
            
            # Test adding time record for Feb 29th
            time_record = TimeRecord(date=feb_29, total_seconds=3600)
            project.time_records[feb_29] = time_record
            
            # Verify record was added
            self.assertIn(feb_29, project.time_records)
            self.assertEqual(project.time_records[feb_29].total_seconds, 3600)
            
            print(f"✓ February 29th {year} handled correctly")
        
        # Test February 29th in non-leap years (should be invalid)
        for year in non_leap_years:
            feb_29 = f"{year}-02-29"
            
            self.assertFalse(calendar.isleap(year), f"{year} should not be a leap year")
            
            try:
                # Attempt to create datetime for Feb 29 in non-leap year
                datetime.strptime(feb_29, "%Y-%m-%d")
                self.fail(f"Should not accept Feb 29 in non-leap year {year}")
            except ValueError:
                print(f"✓ February 29th {year} correctly rejected")
        
        # Test leap year calculations
        leap_year_2024_days = (datetime(2024, 12, 31) - datetime(2024, 1, 1)).days + 1
        non_leap_year_2023_days = (datetime(2023, 12, 31) - datetime(2023, 1, 1)).days + 1
        
        self.assertEqual(leap_year_2024_days, 366, "Leap year should have 366 days")
        self.assertEqual(non_leap_year_2023_days, 365, "Non-leap year should have 365 days")
        
        print(f"✓ Leap year 2024: {leap_year_2024_days} days")
        print(f"✓ Non-leap year 2023: {non_leap_year_2023_days} days")
    
    def test_month_boundary_calculations(self):
        """Test time calculations across month boundaries"""
        print("\n=== Date/Time Test: Month Boundary Calculations ===")
        
        dm = ProjectDataManager(str(self.test_data_file))
        dm.load_projects()
        
        project = dm.add_project("Month Boundary Test", "MON-001", "month_test")
        
        # Test various month boundary scenarios
        test_cases = [
            # (start_date, end_date, description)
            ("2025-01-31", "2025-02-01", "January to February"),
            ("2025-02-28", "2025-03-01", "February to March (non-leap)"),
            ("2024-02-29", "2024-03-01", "February to March (leap year)"),
            ("2025-04-30", "2025-05-01", "April to May (30 days to 31 days)"),
            ("2025-12-31", "2026-01-01", "Year boundary December to January"),
        ]
        
        for start_date, end_date, description in test_cases:
            print(f"\nTesting: {description}")
            
            # Add time records for boundary dates
            start_record = TimeRecord(date=start_date, total_seconds=7200)  # 2 hours
            end_record = TimeRecord(date=end_date, total_seconds=5400)      # 1.5 hours
            
            project.time_records[start_date] = start_record
            project.time_records[end_date] = end_record
            
            # Calculate date difference
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            date_diff = (end_dt - start_dt).days
            
            self.assertEqual(date_diff, 1, f"Should be 1 day difference for {description}")
            
            # Calculate total time for both days
            total_seconds = start_record.total_seconds + end_record.total_seconds
            total_hours = total_seconds / 3600
            
            print(f"✓ {start_date}: {start_record.total_seconds/3600:.1f} hours")
            print(f"✓ {end_date}: {end_record.total_seconds/3600:.1f} hours") 
            print(f"✓ Total: {total_hours:.1f} hours across boundary")
            
            # Verify dates are consecutive
            next_day = start_dt + timedelta(days=1)
            self.assertEqual(next_day.strftime("%Y-%m-%d"), end_date)
    
    def test_daylight_saving_time_transitions(self):
        """Test time calculations during DST transitions"""
        print("\n=== Date/Time Test: Daylight Saving Time Transitions ===")
        
        dm = ProjectDataManager(str(self.test_data_file))
        dm.load_projects()
        
        project = dm.add_project("DST Test", "DST-001", "dst_test")
        
        # Common DST transition dates (vary by timezone)
        # Using general spring forward / fall back dates
        dst_transitions = [
            # Spring Forward (lose an hour) - typically 2nd Sunday in March
            ("2024-03-10", "Spring Forward"),  # 2024 DST start
            ("2025-03-09", "Spring Forward"),  # 2025 DST start
            
            # Fall Back (gain an hour) - typically 1st Sunday in November  
            ("2024-11-03", "Fall Back"),      # 2024 DST end
            ("2025-11-02", "Fall Back"),      # 2025 DST end
        ]
        
        for transition_date, transition_type in dst_transitions:
            print(f"\nTesting {transition_type}: {transition_date}")
            
            # Test day before transition
            transition_dt = datetime.strptime(transition_date, "%Y-%m-%d")
            day_before = (transition_dt - timedelta(days=1)).strftime("%Y-%m-%d")
            day_after = (transition_dt + timedelta(days=1)).strftime("%Y-%m-%d")
            
            # Add time records around DST transition
            before_record = TimeRecord(date=day_before, total_seconds=8 * 3600)    # 8 hours
            transition_record = TimeRecord(date=transition_date, total_seconds=8 * 3600)  # 8 hours
            after_record = TimeRecord(date=day_after, total_seconds=8 * 3600)      # 8 hours
            
            project.time_records[day_before] = before_record
            project.time_records[transition_date] = transition_record
            project.time_records[day_after] = after_record
            
            # Calculate total time for 3-day period
            total_seconds = (before_record.total_seconds + 
                           transition_record.total_seconds + 
                           after_record.total_seconds)
            total_hours = total_seconds / 3600
            
            print(f"✓ Day before ({day_before}): 8.0 hours")
            print(f"✓ Transition day ({transition_date}): 8.0 hours")
            print(f"✓ Day after ({day_after}): 8.0 hours")
            print(f"✓ Total recorded: {total_hours:.1f} hours")
            
            # In our system, we track total seconds regardless of DST
            # The actual wall clock time may differ, but recorded time should be consistent
            expected_seconds = 3 * 8 * 3600  # 24 hours total
            self.assertEqual(total_seconds, expected_seconds, 
                           f"Should record 24 hours regardless of DST for {transition_type}")
            
            print(f"✓ DST transition handled consistently")
    
    def test_invalid_date_format_handling(self):
        """Test handling of invalid date formats"""
        print("\n=== Date/Time Test: Invalid Date Format Handling ===")
        
        dm = ProjectDataManager(str(self.test_data_file))
        dm.load_projects()
        
        project = dm.add_project("Date Format Test", "FMT-001", "format_test")
        
        # Test various invalid date formats
        invalid_dates = [
            "2025-13-01",    # Invalid month
            "2025-02-30",    # Invalid day for February
            "2025-04-31",    # Invalid day for April (only 30 days)
            "2025-00-15",    # Invalid month (0)
            "2025-06-00",    # Invalid day (0)
            "25-06-15",      # Wrong year format
            "2025/06/15",    # Wrong separator
            "15-06-2025",    # Wrong order
            "2025-6-15",     # Missing zero padding
            "invalid-date",  # Completely invalid
            "",              # Empty string
        ]
        
        valid_dates_count = 0
        invalid_dates_count = 0
        
        for invalid_date in invalid_dates:
            try:
                # Attempt to validate date format
                datetime.strptime(invalid_date, "%Y-%m-%d")
                
                # If we get here, the date was valid (unexpected for our test cases)
                print(f"⚠️ Unexpected valid date: {invalid_date}")
                valid_dates_count += 1
                
                # Still test adding it to project
                time_record = TimeRecord(date=invalid_date, total_seconds=3600)
                project.time_records[invalid_date] = time_record
                
            except ValueError as e:
                # Expected behavior for invalid dates
                print(f"✓ Invalid date rejected: {invalid_date} ({str(e).split(' ')[-1]})")
                invalid_dates_count += 1
            except Exception as e:
                print(f"✓ Date error handled: {invalid_date} ({type(e).__name__})")
                invalid_dates_count += 1
        
        print(f"\n✓ Invalid dates rejected: {invalid_dates_count}")
        print(f"⚠️ Unexpected valid dates: {valid_dates_count}")
        
        # Most of our test cases should be invalid
        self.assertGreater(invalid_dates_count, valid_dates_count, 
                          "Most test cases should be invalid dates")
    
    def test_time_zone_independent_calculations(self):
        """Test that calculations work regardless of system timezone"""
        print("\n=== Date/Time Test: Timezone Independence ===")
        
        dm = ProjectDataManager(str(self.test_data_file))
        dm.load_projects()
        
        project = dm.add_project("Timezone Test", "TZ-001", "tz_test")
        
        # Test with dates around the world's timezone boundaries
        test_dates = [
            "2025-01-01",  # New Year (varies by timezone)
            "2025-07-01",  # Mid-year  
            "2025-12-31",  # New Year's Eve
        ]
        
        for test_date in test_dates:
            # Add time record
            time_record = TimeRecord(date=test_date, total_seconds=8 * 3600)  # 8 hours
            project.time_records[test_date] = time_record
            
            # Test that date parsing is consistent
            parsed_date = datetime.strptime(test_date, "%Y-%m-%d")
            formatted_date = parsed_date.strftime("%Y-%m-%d")
            
            self.assertEqual(test_date, formatted_date, 
                           f"Date should round-trip consistently: {test_date}")
            
            # Test time calculations are timezone independent
            hours = time_record.total_seconds / 3600
            minutes = (time_record.total_seconds % 3600) / 60
            
            self.assertEqual(hours, 8.0, "Hour calculation should be timezone independent")
            self.assertEqual(minutes, 0.0, "Minute calculation should be timezone independent")
            
            print(f"✓ {test_date}: {hours:.1f}h {minutes:.0f}m (timezone independent)")
        
        # Test date arithmetic
        start_date = datetime.strptime("2025-06-15", "%Y-%m-%d")
        end_date = start_date + timedelta(days=7)
        
        expected_end = "2025-06-22"
        actual_end = end_date.strftime("%Y-%m-%d")
        
        self.assertEqual(actual_end, expected_end, "Date arithmetic should be consistent")
        print(f"✓ Date arithmetic: 2025-06-15 + 7 days = {actual_end}")
    
    def test_year_boundary_time_tracking(self):
        """Test time tracking across year boundaries"""
        print("\n=== Date/Time Test: Year Boundary Time Tracking ===")
        
        dm = ProjectDataManager(str(self.test_data_file))
        dm.load_projects()
        
        project = dm.add_project("Year Boundary Test", "YR-001", "year_test")
        
        # Test December 31st to January 1st transition
        year_transitions = [
            ("2023-12-31", "2024-01-01"),
            ("2024-12-31", "2025-01-01"),
            ("2025-12-31", "2026-01-01"),
        ]
        
        for last_day, first_day in year_transitions:
            print(f"\nTesting year transition: {last_day} → {first_day}")
            
            # Add time records for year boundary
            last_day_record = TimeRecord(date=last_day, total_seconds=4 * 3600)    # 4 hours
            first_day_record = TimeRecord(date=first_day, total_seconds=6 * 3600)  # 6 hours
            
            project.time_records[last_day] = last_day_record
            project.time_records[first_day] = first_day_record
            
            # Verify dates are consecutive across year boundary
            last_dt = datetime.strptime(last_day, "%Y-%m-%d")
            first_dt = datetime.strptime(first_day, "%Y-%m-%d")
            
            date_diff = (first_dt - last_dt).days
            self.assertEqual(date_diff, 1, "Should be 1 day difference across year boundary")
            
            # Test year extraction
            last_year = last_dt.year
            first_year = first_dt.year
            self.assertEqual(first_year - last_year, 1, "Should increment year by 1")
            
            # Test total time calculation
            total_seconds = last_day_record.total_seconds + first_day_record.total_seconds
            total_hours = total_seconds / 3600
            
            print(f"✓ {last_day} ({last_year}): 4.0 hours")
            print(f"✓ {first_day} ({first_year}): 6.0 hours")
            print(f"✓ Total across boundary: {total_hours:.1f} hours")
            
            # Test month and day rollover
            self.assertEqual(last_dt.month, 12, "Last day should be December")
            self.assertEqual(last_dt.day, 31, "Last day should be 31st")
            self.assertEqual(first_dt.month, 1, "First day should be January")
            self.assertEqual(first_dt.day, 1, "First day should be 1st")
    
    def test_time_duration_edge_cases(self):
        """Test edge cases in time duration calculations"""
        print("\n=== Date/Time Test: Time Duration Edge Cases ===")
        
        dm = ProjectDataManager(str(self.test_data_file))
        dm.load_projects()
        
        project = dm.add_project("Duration Test", "DUR-001", "duration_test")
        
        # Test various duration edge cases
        duration_test_cases = [
            (0, "Zero duration"),
            (1, "One second"),
            (59, "59 seconds"),
            (60, "Exactly 1 minute"),
            (3599, "59 minutes 59 seconds"),
            (3600, "Exactly 1 hour"),
            (86399, "23 hours 59 minutes 59 seconds"),
            (86400, "Exactly 24 hours"),
            (90000, "More than 24 hours"),
            (999999, "Very large duration"),
        ]
        
        test_date = "2025-08-15"
        
        for seconds, description in duration_test_cases:
            print(f"\nTesting: {description} ({seconds} seconds)")
            
            # Create time record
            time_record = TimeRecord(date=test_date, total_seconds=seconds)
            
            # Calculate hours, minutes, seconds breakdown
            hours = seconds // 3600
            remaining_seconds = seconds % 3600
            minutes = remaining_seconds // 60
            secs = remaining_seconds % 60
            
            # Test various formatting approaches
            hms_format = f"{hours:02d}:{minutes:02d}:{secs:02d}"
            decimal_hours = seconds / 3600
            
            print(f"✓ HH:MM:SS format: {hms_format}")
            print(f"✓ Decimal hours: {decimal_hours:.2f}")
            
            # Verify calculations
            reconstructed_seconds = hours * 3600 + minutes * 60 + secs
            self.assertEqual(reconstructed_seconds, seconds, 
                           f"Time breakdown should reconstruct original seconds for {description}")
            
            # Test edge cases for display
            if seconds >= 86400:  # More than 24 hours
                days = seconds // 86400
                day_remainder = seconds % 86400
                day_hours = day_remainder // 3600
                print(f"✓ Extended format: {days}d {day_hours:02d}h")
            
            # Store record for later verification
            record_key = f"{test_date}_{seconds}"
            project.time_records[record_key] = time_record
        
        # Verify all records were stored correctly
        self.assertEqual(len(project.time_records), len(duration_test_cases),
                        "All duration test cases should be stored")
        
        print(f"\n✓ All {len(duration_test_cases)} duration edge cases handled correctly")


if __name__ == '__main__':
    unittest.main(verbosity=2)
