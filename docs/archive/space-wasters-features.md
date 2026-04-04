Here is the man page for a program called Daisy Disk.  I want to make include some of these features if they are useful.  

The most efficient way to free up disk space is to delete some large files and folders you no longer need.

Look at the disk map and try to locate unusually large folders. Then drill down and find out what actually takes so much disk space.

# iTunes and media files
iTunes library often takes tens or hundreds of gigabytes on users’ disks. Here’re a few suggestions on cleaning it:

Check for duplicates. Removing a single film’s copy can save you up to 5 gigabytes.
Remove old backups of your iOS devices. These are normally located within ~/Library/Application Support/MobileSync/Backup.
Delete old purchased content. You don’t have to keep a local copy of every movie, song or app you’ve purchased on iTunes as they can be redownloaded anytime (unless taken down from the store).
Remove some large movies, apps or podcasts. While DaisyDisk can be a great tool for finding the largest ones, use iTunes’ own UI to delete any content from its library to avoid broken links.
Check movie (~/Movies) or music (~/Music) folders for large films, podcasts or music collections you may not need anymore.

# Downloads
Download (~/Downloads) folders are often filled with lots of large files you don’t even know about. It’s usually a good idea to move everything valuable out of this folder and just empty it from time to time. Do you really need to keep all the stuff you download from the network?

# Games
Modern games successfully compete with HD movies for taking most of the disk space. Mac App Store and Steam gamers are lucky: they can delete their games and download them later saving tens of gigabytes on their disks.

Mac App Store games are normally located in your Applications (/Applications) folder and Steam game folder can be found in ~/Library/Application Support/Steam. Just don’t delete Steam games from DaisyDisk, use Steam’s own UI instead.

# Hidden and purgeable space
Sometimes you may notice that a significant part of your disk is taken by so called “hidden space”. You can scan as administrator to reveal the restricted folders.

“Purgeable space” is one of the possible hidden consumers of disk space. macOS will automatically reclaim it when applications require more disk space. Alternatively, you can forcedly reclaim by dragging the “purgeable space” item to the Collector.

# Application libraries and leftovers
Some applications leave huge cache files or libraries in ~/Library/Application Support, but be careful when deleting anything from this folder and know what you’re doing. If you need to remove an application with all of its settings and data, use special tools like AppDelete.

# Collectors
The Collector
You can tear off DaisyDisk’s petals and drop them to the special area at the bottom called “Collector”:

## Empty collector

In addition to drag-and-drop, you can put files and folders to the Collector by selecting the Move “Selected File” to Collector command from the item’s context menu, or by pressing ⌘⌫ hotkey while pointing to an object.

Don’t worry, the files remain intact until you click the Delete button.

## Full collector

You can expand the Collector by clicking on it to make sure you are not about to accidentally delete some needed files. The expanded Collector works just like the sidebar, so you can preview files and drag them out. Another way to get an item out of the Collector is to point and click the × button near its name

## What can you delete?
Some folders like /System, /Library or current user’s home folder are not meant to be deleted, so the Collector will not accept them.

## Collector system message

Semi-transparent (consolidated) petals also cannot be removed, you’ll have to expand the group and drag individual files and folders.

Clicking the Delete button starts deletion process, but you’ll have 5 seconds to change your mind and press Cancel.

DaisyDisk permanently removes files and folders instead of moving them to the system Trash, so that the disk space is actually recovered. These files cannot be “undeleted”, but there are other ways.

##  Free space not appearing after deletion?
Contrary to what you may expect, deleting files in macOS may not immediately produce free space. If Time Machine is enabled on your Mac (which should always be recommended), it will regularly back up your entire disk’s content in so called local snapshots. The snapshots are designed in such a way that they don’t consume additional disk space if there is little change compared to the previous backup.

So, when you delete a file, its copy may still be retained in the local snapshots, and still consume the same amount of disk space. In result, the free space will not grow, but the amount of hidden space, and more specifically, the purgeable space, will increase by the corresponding amount. This is normal — macOS will eventually automatically reclaim the purgeable space when the apps request more disk space. Alternatively, you can forcedly purge it with DaisyDisk.