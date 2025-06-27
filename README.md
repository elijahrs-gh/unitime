## Unitime

#### **WARNING BETA:** This program works but is heavily in beta and still being developed. More features will be coming.

Unitime is a universal hackatime tracker that tracks files instead of IDE's allowing you to use one application to track dozens of IDE's.

___

### Installation

Clone the repo with:

```$ git clone https://github.com/elijahrs-gh/unitime.git```

Install dependencies with:

```$ python -m pip install -r requirements.txt```

Now you are ready to go!

___

### Starting

In a terminal window in the repo file start the hackatime API with:

```$ python run_unitime.py```

Then navigate to the UI folder with:

```$ cd UI```

In there run:

```$ python launcher.py```

A UI will now appear where you can run the application. In the projects tab, add the folder you want to track and in settings set the IDE you are going to be using.

#### IDE SETUP

A small amount of IDE setup with be needed.

**Zed:**

In Zed's settings.json file add the parameters:

```
  "autosave": {
    "after_delay": {
      "milliseconds": 1000
    }
  }
```

**You can now start working on files in your project and it will be automatically tracked to hackatime.hackclub.com!**
