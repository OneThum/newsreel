#!/usr/bin/env python3
"""
Script to add OnboardingView.swift to the Xcode project file
"""

import re
import uuid

# Read the project file
project_path = "Newsreel App/Newsreel.xcodeproj/project.pbxproj"
with open(project_path, 'r') as f:
    content = f.read()

# Generate unique IDs for the file
file_ref_id = "4A2000040"  # OnboardingView.swift file reference
build_file_id = "4A1000040"  # Build file entry

# 1. Add to PBXBuildFile section (after line 59, before "/* End PBXBuildFile section */")
build_file_entry = f"\t\t{build_file_id} /* OnboardingView.swift in Sources */ = {{isa = PBXBuildFile; fileRef = {file_ref_id} /* OnboardingView.swift */; }};\n"

# Find the end of PBXBuildFile section
build_file_pattern = r"(4A1000038 /\* NotificationService\.swift in Sources \*/ = \{isa = PBXBuildFile; fileRef = 4A2000038 /\* NotificationService\.swift \*/; \};\n)(\/\* End PBXBuildFile section \*/)"
content = re.sub(build_file_pattern, r"\1" + build_file_entry + r"\2", content)

# 2. Add to PBXFileReference section (after line 103, before the Info.plist line)
file_ref_entry = f"\t\t{file_ref_id} /* OnboardingView.swift */ = {{isa = PBXFileReference; lastKnownFileType = sourcecode.swift; path = OnboardingView.swift; sourceTree = \"<group>\"; }};\n"

# Find the end of file references (before Info.plist)
file_ref_pattern = r"(4A2000038 /\* NotificationService\.swift \*/ = \{isa = PBXFileReference; lastKnownFileType = sourcecode\.swift; path = NotificationService\.swift; sourceTree = \"<group>\"; \};\n)(\t\t4A3000001)"
content = re.sub(file_ref_pattern, r"\1" + file_ref_entry + r"\2", content)

# 3. Add to PBXSourcesBuildPhase section (in the files array)
sources_build_entry = f"\t\t\t\t{build_file_id} /* OnboardingView.swift in Sources */,\n"

# Find the sources build phase files section
sources_pattern = r"(4A1000038 /\* NotificationService\.swift in Sources \*/,\n)(\t\t\t\);)"
content = re.sub(sources_pattern, r"\1" + sources_build_entry + r"\2", content)

# 4. Add to Views group (find the Views group and add the file)
# This requires finding the Views group children array
views_group_entry = f"\t\t\t\t{file_ref_id} /* OnboardingView.swift */,\n"

# Find Views group - look for the group that contains LoginView.swift, MainAppView.swift, etc.
# We'll add it after LaunchScreenView.swift
views_pattern = r"(4A2000037 /\* LaunchScreenView\.swift \*/,\n)(\t\t\t\);)"
# This might not match if Views group is structured differently, let's search more carefully

# Alternative: Find the Views group by its marker
views_group_pattern = r"(4A5000020 /\* Views \*/ = \{\n\t\t\tisa = PBXGroup;\n\t\t\tchildren = \(\n(?:\t\t\t\t.*\n)*?)(\t\t\t\);)"

match = re.search(views_group_pattern, content)
if match:
    # Add at the end of the children array
    views_section = match.group(1)
    # Check if we need to add it
    if file_ref_id not in views_section:
        # Add before the closing of children array
        content = re.sub(
            r"(4A5000020 /\* Views \*/ = \{\n\t\t\tisa = PBXGroup;\n\t\t\tchildren = \(\n(?:\t\t\t\t.*\n)*?)(\t\t\t\);)",
            r"\1" + views_group_entry + r"\2",
            content
        )

# Write back
with open(project_path, 'w') as f:
    f.write(content)

print("✅ Added OnboardingView.swift to Xcode project")
print(f"   File Reference ID: {file_ref_id}")
print(f"   Build File ID: {build_file_id}")
print(f"   Location: Views/Onboarding/OnboardingView.swift")
