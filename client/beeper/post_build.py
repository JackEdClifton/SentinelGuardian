import os
import shutil
from SCons.Script import Import

Import("env")

def copy_versioned_firmware(source, target, env):
	builds_dir = os.path.join(env['PROJECT_DIR'], "builds")
	os.makedirs(builds_dir, exist_ok=True)

	# Auto-increment build number
	build_file = os.path.join(builds_dir, ".build_number")
	if os.path.exists(build_file):
		with open(build_file, "r") as f:
			build_number = int(f.read()) + 1
	else:
		build_number = 1
	with open(build_file, "w") as f:
		f.write(str(build_number))

	# Get version numbers from CPPDEFINES
	cppdefs = env.get("CPPDEFINES", [])
	major = minor = micro = 0
	for d in cppdefs:
		if isinstance(d, str) and '=' in d:
			key, val = d.split('=', 1)
			if key == "VERSION_MAJOR": major = int(val)
			if key == "VERSION_MINOR": minor = int(val)
			if key == "VERSION_MICRO": micro = int(val)
		elif isinstance(d, (tuple, list)) and len(d) == 2:
			key, val = d
			if key == "VERSION_MAJOR": major = int(val)
			if key == "VERSION_MINOR": minor = int(val)
			if key == "VERSION_MICRO": micro = int(val)

	version_str = f"v{major}.{minor}.{micro}.{build_number}"
	dst_folder = os.path.join(builds_dir, version_str)
	os.makedirs(dst_folder, exist_ok=True)

	# Copy firmware files if they exist
	for ext in [".uf2", ".bin", ".elf"]:
		src = os.path.join(env.subst("$BUILD_DIR"), "firmware" + ext)
		if os.path.exists(src):
			dst = os.path.join(dst_folder, f"beeper-{version_str}{ext}")
			shutil.copy(src, dst)
			print(f"Copied {src} -> {dst}")

# Attach the post-build action to the final firmware target
env.AddPostAction("buildprog", copy_versioned_firmware)
