# SIN - 4R
## Základní seznámení s PHP
```html=
<html>
    <head>
        <meta charset="utf-8">
        <title>Dnes je <?php print(date("d.m.Y")); ?></title>
    </head>
    <body>
    <?php
        date_default_timezone_set('Europe/Prague');
        print("funguju, lol<br>");
        print(date("d.m.Y H:i:s"));
        print("<br>");
        $x = 1;
        $y = 2;
        print($x+$y);
        print("<br>");
        $max = 10;
        for($i=1; $i<=$max; $i++){
            if($i % 3 == 0){
                print("<b>" . $i . "</b>");
            }else{
                print($i);
            }
            if($i==$max){
                print(".");
            }else{
                print(", ");
            }
        }
    ?>
    </body>
</html>
```

## REGEX na email: 
```^[+](420|421)[0-9]{9}+$```