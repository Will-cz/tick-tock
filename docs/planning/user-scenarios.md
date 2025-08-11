# Tick-Tock Widget v0.1.0 - User Scenarios & Workflows

**Project**: Tick-Tock Widget v0.1.0  
**Phase**: 2 - Planning  
**Version**: v0.1.0  
**Date**: August 11, 2025  
**Status**: User Experience Validation - Planning Phase  

---

## 👥 Target User Profiles

### **Primary User: Freelance Developer (Sarah)**
- **Background**: Full-stack developer, works from home office
- **Needs**: Track billable hours for multiple clients, simple time tracking
- **Tech Level**: High - comfortable with software tools
- **Usage Pattern**: 6-8 hours/day, 3-5 projects simultaneously

### **Secondary User: Consultant (Mike)**
- **Background**: Management consultant, travels frequently
- **Needs**: Track project time for reporting, works on laptop
- **Tech Level**: Medium - business software user
- **Usage Pattern**: 4-6 hours/day, 2-3 projects, battery conscious

### **Tertiary User: Researcher (Anna)**
- **Background**: Academic researcher, multiple ongoing studies
- **Needs**: Track research time, organize by grant/project
- **Tech Level**: Medium - academic software user
- **Usage Pattern**: Irregular hours, 4-6 projects, precise tracking

---

## 🎯 Core User Scenarios

### **Scenario 1: Daily Startup (Sarah - Freelance Developer)**

**Context**: Sarah starts her workday at 9 AM, needs to begin tracking time for her current project.

**User Journey**:
1. **9:00 AM** - Sarah opens laptop, Tick-Tock starts automatically
   - *Expected*: Widget appears in familiar position, shows current time
   - *Success Criteria*: Startup < 3 seconds, widget visible and ready

2. **9:01 AM** - Sarah checks yesterday's time totals
   - *Action*: Glances at widget showing "Yesterday: 7.5h"
   - *Expected*: Previous day summary visible without clicking
   - *Success Criteria*: Information immediately visible

3. **9:02 AM** - Sarah starts working on "CLIENT-A Website"
   - *Action*: Clicks project dropdown, selects "CLIENT-A"
   - *Expected*: Project selected, timer ready to start
   - *Success Criteria*: Project selection in 1-2 clicks

4. **9:03 AM** - Sarah begins timing
   - *Action*: Clicks "Start" button
   - *Expected*: Timer begins counting, visual indication of running state
   - *Success Criteria*: Clear visual feedback, timer starts immediately

5. **9:15 AM** - Sarah minimizes widget to focus on work
   - *Action*: Clicks minimize button
   - *Expected*: Widget shrinks to compact mode in system tray
   - *Success Criteria*: Minimal screen space, timer continues running

**Pain Points to Address**:
- Project selection must be fast (no complex dialogs)
- Timer state must be immediately obvious
- Minimized state must not distract from work

---

### **Scenario 2: Project Switching (Mike - Consultant)**

**Context**: Mike is working on a client project when he receives an urgent call about another project requiring immediate attention.

**User Journey**:
1. **2:30 PM** - Mike working on "PROJECT-ALPHA Analysis"
   - *Current State*: Timer running for 1.5 hours on PROJECT-ALPHA
   - *Display*: Widget shows "PROJECT-ALPHA: 01:32:15" and running

2. **2:31 PM** - Urgent call about PROJECT-BETA
   - *Action*: Mike needs to switch projects immediately
   - *Expected*: Quick project switching without losing time data
   - *Success Criteria*: Switch projects in <5 seconds

3. **2:32 PM** - Mike switches to PROJECT-BETA
   - *Action*: Opens project dropdown, selects "PROJECT-BETA"
   - *Expected*: Current timer stops and saves, new timer starts
   - *Success Criteria*: Automatic timer management, no manual stop/start

4. **2:33 PM** - Mike verifies the switch
   - *Action*: Glances at widget
   - *Expected*: Shows "PROJECT-BETA: 00:01:23" and running
   - *Success Criteria*: Clear indication of current project and time

5. **3:45 PM** - Mike finishes urgent work, returns to PROJECT-ALPHA
   - *Action*: Switches back to PROJECT-ALPHA
   - *Expected*: Resumes from where he left off (01:32:15)
   - *Success Criteria*: Time preserved, seamless continuation

**Pain Points to Address**:
- Project switching must be immediate (no confirmation dialogs)
- Time must be preserved accurately
- Current project must be clearly indicated

---

### **Scenario 3: End of Day Reporting (Sarah - Freelance Developer)**

**Context**: Sarah finishes work at 6 PM and needs to generate a time report for her client invoice.

**User Journey**:
1. **5:58 PM** - Sarah finishes current task
   - *Action*: Clicks "Stop" to pause timer
   - *Expected*: Timer stops, time is saved
   - *Success Criteria*: Immediate timer stop, data persistence

2. **5:59 PM** - Sarah reviews today's work
   - *Action*: Looks at widget for daily summary
   - *Expected*: Sees "Today: CLIENT-A: 6.5h, CLIENT-B: 1.2h"
   - *Success Criteria*: Daily totals immediately visible

3. **6:00 PM** - Sarah needs detailed report
   - *Action*: Clicks "Report" button
   - *Expected*: Report window opens with today's breakdown
   - *Success Criteria*: Report opens <2 seconds, shows accurate data

4. **6:02 PM** - Sarah exports data for invoicing
   - *Action*: Clicks "Export CSV" in report window
   - *Expected*: File dialog opens, saves time data
   - *Success Criteria*: CSV export works, data formatted correctly

5. **6:03 PM** - Sarah closes application
   - *Action*: Clicks "X" to close widget
   - *Expected*: Data saves automatically, clean shutdown
   - *Success Criteria*: No data loss, clean exit

**Pain Points to Address**:
- Daily summaries must be immediately visible
- Report generation must be fast
- Export must be reliable and formatted correctly

---

### **Scenario 4: System Interruption Recovery (Mike - Consultant)**

**Context**: Mike is working on his laptop when the battery dies unexpectedly, losing unsaved work.

**User Journey**:
1. **11:30 AM** - Mike working on "STRATEGY-DOC"
   - *Current State*: Timer running for 2.5 hours
   - *System State*: Laptop battery at 5%, running on battery

2. **11:45 AM** - Laptop shuts down due to battery
   - *Event*: Sudden system shutdown, no graceful exit
   - *Data Risk*: 15 minutes of time tracking could be lost
   - *Expected*: Auto-save should have preserved data

3. **12:30 PM** - Mike plugs in and restarts laptop
   - *Action*: System boots, Tick-Tock starts automatically
   - *Expected*: Application recovers previous state
   - *Success Criteria*: No data loss, timer state recovered

4. **12:31 PM** - Mike checks time data
   - *Action*: Opens widget, reviews project time
   - *Expected*: Shows "STRATEGY-DOC: 02:45:00" (accurate to last save)
   - *Success Criteria*: Maximum 5-minute data loss

5. **12:32 PM** - Mike resumes work
   - *Action*: Starts timer for current project
   - *Expected*: Continues normally, no impact on workflow
   - *Success Criteria*: Seamless recovery, normal operation

**Pain Points to Address**:
- Auto-save must be frequent enough to minimize data loss
- Recovery must be automatic and transparent
- Timer state must be preserved across system interruptions

---

### **Scenario 5: Multi-project Day (Anna - Researcher)**

**Context**: Anna has a complex research day with meetings, writing, and analysis across multiple grants.

**User Journey**:
1. **9:00 AM** - Anna starts with "GRANT-A Literature Review"
   - *Action*: Selects project, starts timer
   - *Expected*: Timer starts for literature review work
   - *Duration*: 2 hours planned

2. **11:00 AM** - Interruption: Urgent email about GRANT-B
   - *Action*: Quickly switches to "GRANT-B Administrative"
   - *Expected*: Automatic project switch, time saved
   - *Duration*: 30 minutes unplanned

3. **11:30 AM** - Returns to literature review
   - *Action*: Switches back to "GRANT-A Literature Review"
   - *Expected*: Resumes where left off
   - *Duration*: 30 minutes more

4. **12:00 PM** - Lunch break
   - *Action*: Stops timer completely
   - *Expected*: All time saved, timer paused
   - *Duration*: 1 hour break

5. **1:00 PM** - Afternoon: "GRANT-C Data Analysis"
   - *Action*: Starts new project timer
   - *Expected*: Fresh timer for different project
   - *Duration*: 3 hours planned

6. **4:00 PM** - Unexpected meeting about GRANT-A
   - *Action*: Switches to "GRANT-A Meetings"
   - *Expected*: Different sub-activity for same grant
   - *Duration*: 1 hour unplanned

7. **5:00 PM** - End of day review
   - *Action*: Reviews daily time distribution
   - *Expected*: Sees breakdown by grant and activity type
   - *Success Criteria*: Accurate time allocation for grant reporting

**Pain Points to Address**:
- Frequent project switching must be seamless
- Sub-activities within projects must be supported
- Daily summaries must show project breakdown
- Data must be suitable for grant/funding reports

---

## 💡 Key Insights from Scenarios

### **Critical User Needs**:
1. **Speed**: All operations must be fast (<5 seconds)
2. **Reliability**: Data must never be lost
3. **Clarity**: Current state must always be obvious
4. **Simplicity**: Common tasks must be 1-2 clicks
5. **Recovery**: System must handle interruptions gracefully

### **Most Important Features (Based on Scenarios)**:
1. **Reliable Project Switching** - Used constantly throughout day
2. **Automatic Time Preservation** - Critical for data integrity
3. **Clear State Indicators** - Essential for user confidence
4. **Quick Daily Summaries** - Needed for end-of-day review
5. **System Recovery** - Essential for mobile/laptop users

### **Features That Can Be Simplified**:
1. **Complex Reporting** - Basic CSV export sufficient for v0.1.0
2. **Advanced Timer Features** - Pomodoro, goals can wait
3. **Customization Options** - Basic theming sufficient initially
4. **Collaboration Features** - Not needed for single-user scenarios

---

## 🎯 Scenario-Based Acceptance Criteria

### **For Feature: Project Switching**
- [ ] Switch projects in <3 seconds (Mike's urgent call scenario)
- [ ] Preserve time to last auto-save (max 5-minute loss)
- [ ] Visual confirmation of switch (clear current project display)
- [ ] No confirmation dialogs for common switches

### **For Feature: System Recovery**
- [ ] Recover from unexpected shutdown (Mike's battery scenario)
- [ ] Preserve timer state across system sleep/wake
- [ ] Auto-save frequent enough to minimize loss (<5 minutes)
- [ ] Transparent recovery (no user intervention required)

### **For Feature: Daily Summaries**
- [ ] Show today's totals without clicking (Sarah's daily review)
- [ ] Update in real-time as timer runs
- [ ] Group by project with clear totals
- [ ] Format suitable for quick decision-making

---

*These scenarios validate that requirements address real user needs and provide concrete acceptance criteria based on actual usage patterns.*
