# Project Diary: A/B Test Experimentation

**June 2026**

---

I want to be honest about why I built this project. It was not just to add something to my portfolio. It was because I realised I did not really understand how experimentation works in a product team. I could talk about A/B tests at a surface level in interviews but I had never actually designed one, run the numbers, or sat with the results. This was my attempt to fix that.

Starting out, what excited me was the idea that this is how real decisions get made. Not one person deciding something looks right on a dashboard, but a proper process where different stakeholders can look at the same data and challenge what they see. Control versus treatment. Did it work or did it not? The structure of it appealed to me. It felt grown up in a way that building a dimensional model does not quite capture, because with experimentation there is a right answer buried in the data and your job is to find it honestly.

The moment that clicked most for me was in the Jupyter notebooks. I have used Python before but I tend to treat it like a calculator, paste some code in and hope it runs. Working through the EDA and then the statistical tests felt different. When the z-test ran and I could see the p-value and read what it actually meant, something shifted. The numbers were not abstract anymore. I was looking at 463 real orders split across two groups and asking whether the difference between them was meaningful or just noise. That felt like proper analysis, not just formatting.

The most frustrating part was nothing glamorous. It was the git push and pull errors. Multiple times I ran commands from the wrong folder, got errors I did not understand, had to close things down and start again. There was one moment where Vim opened in the terminal and I could not exit it and ended up closing the whole Command Prompt window. It sounds trivial but when you are trying to build momentum it breaks your flow completely. I know my way around git much better now than I did at the start of this, which is probably the most practical thing I am taking away.

The 1,210 day finding from the power calculation was unexpected. My first reaction was that I had done something wrong. I went back through the formula twice. I had not done anything wrong. The standard deviation of order values in this dataset is higher than the mean, which means you need a huge sample to detect a small effect. What I took from it was not that the project failed but that this is exactly the kind of thing you need to check before you write a line of code. The traffic volume and the variance in your metric determine whether your experiment is even worth running. I will think about that differently now.

If I started this again I would tell myself one thing: be ready for the result to tell you something you did not expect, and do not try to make it say something else. The right answer here was inconclusive. The experiment was underpowered. That is the honest finding and I documented it honestly rather than pretending the tiny differences I saw were meaningful. In the same way that I would want a stakeholder to give me honest feedback on a dashboard even if it is not what I wanted to hear, the data deserves the same respect. A negative result properly explained is more useful than a positive result that is not real.

---

*This diary entry was written as part of the project publish process. The technical write-up is in `README_AB_TEST.md`.*
